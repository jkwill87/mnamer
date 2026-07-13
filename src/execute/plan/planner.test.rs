//! Verifies metadata resolution, grouping, and destination planning.

use super::*;
use crate::execute::format::FormatOptions;
use crate::execute::plan::FirstCandidateSelector;
use crate::net::provider::{Candidate, CandidateError};
use async_trait::async_trait;
use std::collections::VecDeque;
use std::path::Path;
use std::sync::Mutex;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Duration;

#[derive(Default)]
struct FakeSource {
    delays: Mutex<Vec<(String, u64)>>,
    empty: bool,
    calls: Arc<AtomicUsize>,
}

#[async_trait]
impl CandidateSource for FakeSource {
    async fn search(
        &self,
        provider: ProviderKind,
        query: &Metadata,
        _max_results: usize,
    ) -> Result<Vec<Candidate>, CandidateError> {
        self.calls.fetch_add(1, Ordering::Relaxed);
        let identity = query.display_name().to_owned();
        let delay = self
            .delays
            .lock()
            .unwrap()
            .iter()
            .find_map(|(name, delay)| (name == &identity).then_some(*delay))
            .unwrap_or_default();
        tokio::time::sleep(Duration::from_millis(delay)).await;
        if self.empty {
            return Ok(Vec::new());
        }
        Ok(vec![Candidate {
            provider,
            metadata: Metadata {
                media_type: query.media_type,
                name: query.name.clone(),
                series: query.series.clone(),
                season: query.season,
                episode: query.episode,
                title: (query.media_type == MediaKind::Episode).then(|| "Pilot".into()),
                year: query.year,
                ..Metadata::default()
            },
            score: Some(1.0),
        }])
    }
}

struct FailingSource;

#[async_trait]
impl CandidateSource for FailingSource {
    async fn search(
        &self,
        _provider: ProviderKind,
        _query: &Metadata,
        _max_results: usize,
    ) -> Result<Vec<Candidate>, CandidateError> {
        Err(CandidateError::new("provider unavailable"))
    }
}

fn planner(source: FakeSource, mut options: PlanningOptions) -> Planner {
    options.batch = true;
    Planner::new(
        Arc::new(source),
        Arc::new(FirstCandidateSelector),
        DestinationFormatter::new(FormatOptions::default()).unwrap(),
        options,
    )
}

#[tokio::test]
async fn batch_restores_discovery_order_after_concurrent_resolution() {
    let directory = tempfile::tempdir().unwrap();
    let first = directory.path().join("Elemental.2023.mkv");
    let second = directory.path().join("Malignant.2021.mkv");
    std::fs::write(&first, b"").unwrap();
    std::fs::write(&second, b"").unwrap();
    let source = FakeSource {
        delays: Mutex::new(vec![("Elemental".into(), 30), ("Malignant".into(), 1)]),
        empty: false,
        ..FakeSource::default()
    };

    let result = planner(source, PlanningOptions::default())
        .plan(vec![first.clone(), second.clone()])
        .await
        .unwrap();

    assert_eq!(result.items[0].source, first);
    assert_eq!(result.items[1].source, second);
    assert!(
        result
            .items
            .iter()
            .all(|item| item.outcome == OperationOutcome::Ready)
    );
}

#[tokio::test]
async fn batch_provider_miss_requires_allow_guess() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("The.Prince.of.Egypt.1998.mkv");
    std::fs::write(&source, b"").unwrap();
    let result = planner(
        FakeSource {
            empty: true,
            ..FakeSource::default()
        },
        PlanningOptions::default(),
    )
    .plan(vec![source])
    .await
    .unwrap();

    assert_eq!(result.items[0].outcome, OperationOutcome::Unmatched);
}

#[tokio::test]
async fn allow_guess_uses_parsed_metadata_on_provider_miss() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Mars.Attacks.1996.mkv");
    std::fs::write(&source, b"").unwrap();
    let options = PlanningOptions {
        allow_guess: true,
        ..PlanningOptions::default()
    };
    let result = planner(
        FakeSource {
            empty: true,
            ..FakeSource::default()
        },
        options,
    )
    .plan(vec![source])
    .await
    .unwrap();

    assert_eq!(result.items[0].outcome, OperationOutcome::Ready);
    assert_eq!(result.items[0].match_origin, Some(MatchOrigin::Guess));
}

#[tokio::test]
async fn allow_guess_does_not_hide_provider_transport_errors() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Prometheus.2012.mkv");
    std::fs::write(&source, b"").unwrap();
    let options = PlanningOptions {
        allow_guess: true,
        batch: true,
        ..PlanningOptions::default()
    };
    let planner = Planner::new(
        Arc::new(FailingSource),
        Arc::new(FirstCandidateSelector),
        DestinationFormatter::new(FormatOptions::default()).unwrap(),
        options,
    );

    let result = planner.plan(vec![source]).await.unwrap();

    assert_eq!(result.items[0].outcome, OperationOutcome::Failed);
    assert_eq!(result.items[0].provider, Some(ProviderKind::Tmdb));
}

#[test]
fn subtitles_are_grouped_with_their_matching_video() {
    let directory = tempfile::tempdir().unwrap();
    let parsed = vec![
        ParsedItem {
            index: 0,
            source: directory.path().join("Requiem.for.a.Dream.2000.mkv"),
            metadata: Metadata::inspect(
                &directory.path().join("Requiem.for.a.Dream.2000.mkv"),
                None,
            ),
        },
        ParsedItem {
            index: 1,
            source: directory.path().join("Requiem.for.a.Dream.2000.en.srt"),
            metadata: Metadata::inspect(
                &directory.path().join("Requiem.for.a.Dream.2000.en.srt"),
                None,
            ),
        },
    ];

    let groups = group_subtitles(&parsed);

    assert_eq!(groups.len(), 1);
    assert_eq!(groups[0].members, vec![0, 1]);
}

#[tokio::test]
async fn associated_subtitles_share_metadata_and_keep_language_suffix() {
    let directory = tempfile::tempdir().unwrap();
    let video = directory.path().join("The.Thirteenth.Floor.1999.mkv");
    let subtitle = directory.path().join("The.Thirteenth.Floor.1999.en.srt");
    std::fs::write(&video, b"video").unwrap();
    std::fs::write(&subtitle, b"subtitle").unwrap();

    let result = planner(FakeSource::default(), PlanningOptions::default())
        .plan(vec![video, subtitle])
        .await
        .unwrap();

    assert_eq!(result.items.len(), 2);
    assert!(
        result
            .items
            .iter()
            .all(|item| item.outcome == OperationOutcome::Ready)
    );
    assert_eq!(
        result.items[1]
            .destination
            .as_ref()
            .unwrap()
            .file_name()
            .unwrap(),
        "The Thirteenth Floor (1999).en.srt"
    );
}

#[tokio::test]
async fn batch_skips_subtitles_without_a_language_marker() {
    let directory = tempfile::tempdir().unwrap();
    let video = directory.path().join("Night.in.Paradise.2020.mkv");
    let subtitle = directory.path().join("Night.in.Paradise.2020.srt");
    std::fs::write(&video, b"video").unwrap();
    std::fs::write(&subtitle, b"").unwrap();

    let result = planner(FakeSource::default(), PlanningOptions::default())
        .plan(vec![video, subtitle])
        .await
        .unwrap();

    assert_eq!(result.items[0].outcome, OperationOutcome::Ready);
    assert_eq!(result.items[1].outcome, OperationOutcome::Skipped);
}

#[tokio::test]
async fn batch_uses_detected_subtitle_content_language() {
    let directory = tempfile::tempdir().unwrap();
    let video = directory.path().join("Night.in.Paradise.2020.mkv");
    let subtitle = directory.path().join("Night.in.Paradise.2020.srt");
    std::fs::write(&video, b"video").unwrap();
    std::fs::write(
        &subtitle,
        b"1\n00:00:01,000 --> 00:00:04,000\nThe morning train arrived at the station while everyone waited patiently on the platform.\n",
    )
    .unwrap();

    let result = planner(FakeSource::default(), PlanningOptions::default())
        .plan(vec![video, subtitle])
        .await
        .unwrap();

    assert_eq!(result.items[0].outcome, OperationOutcome::Ready);
    assert_eq!(result.items[1].outcome, OperationOutcome::Ready);
    assert_eq!(result.items[1].metadata.language_sub.as_deref(), Some("en"));
    assert!(
        result.items[1]
            .destination
            .as_ref()
            .unwrap()
            .ends_with("Night in Paradise (2020).en.srt")
    );
}

#[test]
fn normalizes_stems_and_associates_generic_and_nested_subtitles_unambiguously() {
    let directory = tempfile::tempdir().unwrap();
    let movie = directory.path().join("The.Emperors.New.Groove.2000.mkv");
    let generic = directory.path().join("English.srt");
    let nested = directory
        .path()
        .join("Subs/The Emperors New Groove.eng.forced.ass");
    let parsed = [movie, generic, nested]
        .into_iter()
        .enumerate()
        .map(|(index, source)| ParsedItem {
            index,
            metadata: Metadata::inspect(&source, None),
            source,
        })
        .collect::<Vec<_>>();

    let groups = group_subtitles(&parsed);

    assert_eq!(groups.len(), 1);
    assert_eq!(groups[0].members, vec![0, 1, 2]);
}

#[test]
fn associates_subtitles_below_deep_language_and_disposition_directories() {
    let directory = tempfile::tempdir().unwrap();
    let media_directory = directory.path().join("Batman Returns (1992)");
    let parsed = [
        media_directory.join("Batman.Returns.1992.mkv"),
        media_directory.join("Subs/English/Forced/track.srt"),
    ]
    .into_iter()
    .enumerate()
    .map(|(index, source)| ParsedItem {
        index,
        metadata: Metadata::inspect(&source, None),
        source,
    })
    .collect::<Vec<_>>();

    let groups = group_subtitles(&parsed);

    assert_eq!(groups.len(), 1);
    assert_eq!(groups[0].members, vec![0, 1]);
    assert_eq!(parsed[1].metadata.language_sub.as_deref(), Some("en"));
    assert_eq!(
        parsed[1].metadata.subtitle_dispositions,
        [crate::media::SubtitleDisposition::Forced]
    );
}

#[test]
fn associates_subtitles_below_a_direct_language_directory() {
    let directory = tempfile::tempdir().unwrap();
    let media_directory = directory.path().join("Roll Bounce (2005)");
    let parsed = [
        media_directory.join("Roll.Bounce.2005.mkv"),
        media_directory.join("English/track.srt"),
    ]
    .into_iter()
    .enumerate()
    .map(|(index, source)| ParsedItem {
        index,
        metadata: Metadata::inspect(&source, None),
        source,
    })
    .collect::<Vec<_>>();

    let groups = group_subtitles(&parsed);

    assert_eq!(groups.len(), 1);
    assert_eq!(groups[0].members, vec![0, 1]);
    assert_eq!(parsed[1].metadata.name.as_deref(), Some("Roll Bounce"));
    assert_eq!(parsed[1].metadata.year, Some(2005));
    assert_eq!(parsed[1].metadata.language_sub.as_deref(), Some("en"));
}

#[test]
fn generic_subtitle_is_not_attached_when_multiple_videos_are_eligible() {
    let directory = tempfile::tempdir().unwrap();
    let parsed = [
        directory.path().join("Scrooged.1988.mkv"),
        directory.path().join("U.S.Marshals.1998.mkv"),
        directory.path().join("English.srt"),
    ]
    .into_iter()
    .enumerate()
    .map(|(index, source)| ParsedItem {
        index,
        metadata: Metadata::inspect(&source, None),
        source,
    })
    .collect::<Vec<_>>();

    let groups = group_subtitles(&parsed);

    assert_eq!(groups.len(), 3);
}

#[test]
fn sole_video_fallback_handles_edition_and_diacritic_stem_differences() {
    for (video, subtitle) in [
        (
            "Doctor.Sleep.Directors.Cut.2019.mkv",
            "Doctor.Sleep.2019.en.srt",
        ),
        ("Amélie.2001.mkv", "Amelie.2001.en.srt"),
        ("Łódź.2022.mkv", "Lodz.2022.en.srt"),
        ("Đavolji.2023.mkv", "Davolji.2023.en.srt"),
        ("Ğişe.2024.mkv", "Gise.2024.en.srt"),
    ] {
        let directory = tempfile::tempdir().unwrap();
        let parsed = [
            directory.path().join(video),
            directory.path().join(subtitle),
        ]
        .into_iter()
        .enumerate()
        .map(|(index, source)| ParsedItem {
            index,
            metadata: Metadata::inspect(&source, None),
            source,
        })
        .collect::<Vec<_>>();

        let groups = group_subtitles(&parsed);

        assert_eq!(groups.len(), 1, "{video} / {subtitle}");
        assert_eq!(groups[0].members, vec![0, 1], "{video} / {subtitle}");
    }
}

#[test]
fn unique_fuzzy_match_is_selected_when_multiple_videos_are_eligible() {
    for (video, subtitle, other) in [
        (
            "Salò.or.the.120.Days.of.Sodom.1976.mkv",
            "Salo.or.the.120.Days.of.Sodom.1976.en.srt",
            "The.Lake.House.2006.mkv",
        ),
        (
            "The.Godfather.Part.III.Coda.1990.mkv",
            "The.Godfather.Part.III.1990.en.srt",
            "Gone.Baby.Gone.2007.mkv",
        ),
    ] {
        let directory = tempfile::tempdir().unwrap();
        let parsed = [
            directory.path().join(video),
            directory.path().join(other),
            directory.path().join(subtitle),
        ]
        .into_iter()
        .enumerate()
        .map(|(index, source)| ParsedItem {
            index,
            metadata: Metadata::inspect(&source, None),
            source,
        })
        .collect::<Vec<_>>();

        let groups = group_subtitles(&parsed);

        assert_eq!(groups.len(), 2, "{video} / {subtitle}");
        assert_eq!(groups[0].members, vec![0, 2], "{video} / {subtitle}");
        assert_eq!(groups[1].members, vec![1], "{video} / {subtitle}");
    }
}

#[test]
fn sole_video_fallback_rejects_explicitly_conflicting_identities() {
    for (video, subtitle) in [
        (
            "The.Cabin.in.the.Woods.2012.mkv",
            "The.Addams.Family.2.2021.en.srt",
        ),
        ("The.Simpsons.S32E01.mkv", "The.Simpsons.S32E02.en.srt"),
        ("The.Game.1997.mkv", "The.Hunt.2020.en.srt"),
        ("Scream.2022.mkv", "Scream.7.2026.en.srt"),
    ] {
        let directory = tempfile::tempdir().unwrap();
        let parsed = [
            directory.path().join(video),
            directory.path().join(subtitle),
        ]
        .into_iter()
        .enumerate()
        .map(|(index, source)| ParsedItem {
            index,
            metadata: Metadata::inspect(&source, None),
            source,
        })
        .collect::<Vec<_>>();

        let groups = group_subtitles(&parsed);

        assert_eq!(groups.len(), 2, "{video} / {subtitle}");
    }
}

#[test]
fn standalone_idx_and_sub_companions_are_one_logical_target() {
    let directory = tempfile::tempdir().unwrap();
    let parsed = [
        directory.path().join("Eng.idx"),
        directory.path().join("English.sub"),
    ]
    .into_iter()
    .enumerate()
    .map(|(index, source)| ParsedItem {
        index,
        metadata: Metadata::inspect(&source, None),
        source,
    })
    .collect::<Vec<_>>();

    let groups = group_subtitles(&parsed);

    assert_eq!(groups.len(), 1);
    assert_eq!(groups[0].members, vec![0, 1]);
}

#[tokio::test]
async fn subtitle_bundle_uses_one_provider_request_and_unique_disposition_destinations() {
    let directory = tempfile::tempdir().unwrap();
    let paths = [
        directory
            .path()
            .join("Hotel.Transylvania.Transformania.2022.mkv"),
        directory
            .path()
            .join("Hotel.Transylvania.Transformania.2022.en.srt"),
        directory
            .path()
            .join("Hotel.Transylvania.Transformania.2022.en.forced.srt"),
        directory
            .path()
            .join("Hotel.Transylvania.Transformania.2022.en.1.srt"),
        directory
            .path()
            .join("Hotel.Transylvania.Transformania.2022.en.2.srt"),
        directory
            .path()
            .join("Hotel.Transylvania.Transformania.2022.en.idx"),
        directory
            .path()
            .join("Hotel.Transylvania.Transformania.2022.en.sub"),
    ];
    for path in &paths {
        std::fs::write(path, path.to_string_lossy().as_bytes()).unwrap();
    }
    let calls = Arc::new(AtomicUsize::new(0));
    let source = FakeSource {
        calls: Arc::clone(&calls),
        ..FakeSource::default()
    };

    let result = planner(source, PlanningOptions::default())
        .plan(paths.into_iter().collect())
        .await
        .unwrap();

    assert_eq!(calls.load(Ordering::Relaxed), 1);
    assert_eq!(result.items.len(), 7);
    assert!(
        result
            .items
            .iter()
            .all(|item| item.outcome == OperationOutcome::Ready)
    );
    let destinations = result
        .items
        .iter()
        .map(|item| item.destination.as_ref().unwrap().clone())
        .collect::<std::collections::HashSet<_>>();
    assert_eq!(destinations.len(), 7);
    assert!(
        destinations
            .iter()
            .any(|path| path.ends_with("Hotel Transylvania Transformania (2022).en.forced.srt"))
    );
    assert!(
        destinations
            .iter()
            .any(|path| path.ends_with("Hotel Transylvania Transformania (2022).en.1.srt"))
    );
    assert!(
        destinations
            .iter()
            .any(|path| path.ends_with("Hotel Transylvania Transformania (2022).en.2.srt"))
    );
}

#[derive(Default)]
struct ScriptedSelector {
    selections: Mutex<VecDeque<CandidateChoice>>,
    subtitle_languages: Mutex<VecDeque<SubtitleLanguageChoice>>,
    offered_guess: Mutex<Vec<bool>>,
    processing_announcements: AtomicUsize,
    subtitle_prompts: AtomicUsize,
}

impl CandidateSelector for ScriptedSelector {
    fn processing(&self, _source: &Path, _metadata: &Metadata) {
        self.processing_announcements
            .fetch_add(1, Ordering::Relaxed);
    }

    fn select(
        &self,
        _source: &Path,
        _candidates: &[Candidate],
        _guess: &Metadata,
        offer_guess: bool,
    ) -> CandidateChoice {
        self.offered_guess.lock().unwrap().push(offer_guess);
        self.selections
            .lock()
            .unwrap()
            .pop_front()
            .unwrap_or(CandidateChoice::Skip)
    }

    fn subtitle_language(&self, _source: &Path) -> SubtitleLanguageChoice {
        self.subtitle_prompts.fetch_add(1, Ordering::Relaxed);
        self.subtitle_languages
            .lock()
            .unwrap()
            .pop_front()
            .unwrap_or(SubtitleLanguageChoice::Skip)
    }
}

#[tokio::test]
async fn interactive_vobsub_pair_shares_one_language_choice() {
    let directory = tempfile::tempdir().unwrap();
    let paths = [
        directory.path().join("The.Batman.2022.mkv"),
        directory.path().join("The.Batman.2022.idx"),
        directory.path().join("The.Batman.2022.sub"),
    ];
    for path in &paths {
        std::fs::write(path, b"fixture").unwrap();
    }
    let selector = Arc::new(ScriptedSelector {
        selections: Mutex::new(VecDeque::from([CandidateChoice::Candidate(0)])),
        subtitle_languages: Mutex::new(VecDeque::from([SubtitleLanguageChoice::Language(
            mediakit::meta::fields::Language::from_identifier("en").unwrap(),
        )])),
        ..ScriptedSelector::default()
    });
    let planner = Planner::new(
        Arc::new(FakeSource::default()),
        selector.clone(),
        DestinationFormatter::new(FormatOptions::default()).unwrap(),
        PlanningOptions::default(),
    );

    let result = planner.plan(paths.into_iter().collect()).await.unwrap();

    assert_eq!(selector.subtitle_prompts.load(Ordering::Relaxed), 1);
    assert!(
        result
            .items
            .iter()
            .all(|item| item.outcome == OperationOutcome::Ready)
    );
    assert_eq!(result.items[1].metadata.language_sub.as_deref(), Some("en"));
    assert_eq!(result.items[2].metadata.language_sub.as_deref(), Some("en"));
    assert!(
        result.items[1]
            .destination
            .as_ref()
            .unwrap()
            .ends_with("The Batman (2022).en.idx")
    );
    assert!(
        result.items[2]
            .destination
            .as_ref()
            .unwrap()
            .ends_with("The Batman (2022).en.sub")
    );
}

#[tokio::test]
async fn interactive_provider_miss_offers_confirmed_guess_without_allow_guess() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("A.Haunting.in.Venice.2023.mkv");
    std::fs::write(&path, b"movie").unwrap();
    let selector = Arc::new(ScriptedSelector {
        selections: Mutex::new(VecDeque::from([CandidateChoice::Guess])),
        ..ScriptedSelector::default()
    });
    let planner = Planner::new(
        Arc::new(FakeSource {
            empty: true,
            ..FakeSource::default()
        }),
        selector.clone(),
        DestinationFormatter::new(FormatOptions::default()).unwrap(),
        PlanningOptions::default(),
    );

    let result = planner.plan(vec![path]).await.unwrap();

    assert_eq!(result.items[0].outcome, OperationOutcome::Ready);
    assert_eq!(result.items[0].match_origin, Some(MatchOrigin::Guess));
    assert_eq!(*selector.offered_guess.lock().unwrap(), [true]);
    assert_eq!(selector.processing_announcements.load(Ordering::Relaxed), 1);
}

#[tokio::test]
async fn interactive_subtitle_language_choices_apply_and_quit_cleanly() {
    let directory = tempfile::tempdir().unwrap();
    let paths = [
        directory.path().join("The.Forever.Purge.2021.mkv"),
        directory.path().join("The.Forever.Purge.2021.srt"),
        directory.path().join("The.Forever.Purge.2021.ass"),
        directory.path().join("Lightyear.2022.mkv"),
    ];
    for path in &paths {
        let contents: &[u8] = if path.extension().is_some_and(|value| value == "mkv") {
            b"fixture"
        } else {
            b""
        };
        std::fs::write(path, contents).unwrap();
    }
    let selector = Arc::new(ScriptedSelector {
        selections: Mutex::new(VecDeque::from([
            CandidateChoice::Candidate(0),
            CandidateChoice::Candidate(0),
        ])),
        subtitle_languages: Mutex::new(VecDeque::from([
            SubtitleLanguageChoice::Language(
                mediakit::meta::fields::Language::from_identifier("en").unwrap(),
            ),
            SubtitleLanguageChoice::Quit,
        ])),
        ..ScriptedSelector::default()
    });
    let planner = Planner::new(
        Arc::new(FakeSource::default()),
        selector,
        DestinationFormatter::new(FormatOptions::default()).unwrap(),
        PlanningOptions::default(),
    );

    let result = planner.plan(paths.into_iter().collect()).await.unwrap();

    assert!(result.quit, "{result:?}");
    assert_eq!(result.items[0].outcome, OperationOutcome::Ready);
    assert_eq!(result.items[1].outcome, OperationOutcome::Ready);
    assert_eq!(result.items[1].metadata.language_sub.as_deref(), Some("en"));
    assert_eq!(result.items[2].outcome, OperationOutcome::Skipped);
    assert_eq!(result.items[3].outcome, OperationOutcome::Skipped);
}

#[tokio::test]
async fn interactive_subtitle_skip_and_interrupt_are_distinct() {
    for (choice, interrupted, video_name, subtitle_name) in [
        (
            SubtitleLanguageChoice::Skip,
            false,
            "District.9.2009.mkv",
            "District.9.2009.srt",
        ),
        (
            SubtitleLanguageChoice::Interrupted,
            true,
            "Drive.2011.mkv",
            "Drive.2011.srt",
        ),
    ] {
        let directory = tempfile::tempdir().unwrap();
        let video = directory.path().join(video_name);
        let subtitle = directory.path().join(subtitle_name);
        std::fs::write(&video, b"video").unwrap();
        std::fs::write(&subtitle, b"").unwrap();
        let selector = Arc::new(ScriptedSelector {
            selections: Mutex::new(VecDeque::from([CandidateChoice::Candidate(0)])),
            subtitle_languages: Mutex::new(VecDeque::from([choice])),
            ..ScriptedSelector::default()
        });
        let planner = Planner::new(
            Arc::new(FakeSource::default()),
            selector,
            DestinationFormatter::new(FormatOptions::default()).unwrap(),
            PlanningOptions::default(),
        );

        let result = planner.plan(vec![video, subtitle]).await.unwrap();

        assert_eq!(result.interrupted, interrupted);
        assert_eq!(result.items[0].outcome, OperationOutcome::Ready);
        assert_eq!(result.items[1].outcome, OperationOutcome::Skipped);
    }
}
