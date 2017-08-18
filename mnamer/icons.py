from collections.abc import Mapping
from tkinter import PhotoImage


class Icons(Mapping):
    def __iter__(self):
        return self.__store.__iter__()

    def __len__(self):
        return self.__store.__len__()

    def __getitem__(self, key) -> PhotoImage:
        return self.__store[key]

    _ICON_ADD_FILE = """
    R0lGODlhKAAoALMJAP///3iLnPT195uptYubqYycqp+tuYqaqaCuuv///wAAAAAAAAAAAAAAAAAA
    AAAAACH/C1hNUCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpy
    ZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0
    az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQw
    ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIv
    MjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4
    bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMu
    YWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94
    YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3No
    b3AgQ0MgMjAxNS41IChXaW5kb3dzKSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpEQjc2NENC
    Q0IxMzcxMUU2ODk2NUY5RTAwMjUzNDZFOSIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpEQjc2
    NENCREIxMzcxMUU2ODk2NUY5RTAwMjUzNDZFOSI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjpp
    bnN0YW5jZUlEPSJ4bXAuaWlkOkRCNzY0Q0JBQjEzNzExRTY4OTY1RjlFMDAyNTM0NkU5IiBzdFJl
    Zjpkb2N1bWVudElEPSJ4bXAuZGlkOkRCNzY0Q0JCQjEzNzExRTY4OTY1RjlFMDAyNTM0NkU5Ii8+
    IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5k
    PSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/O
    zczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGwr66trKuqqainpqWko6KhoJ+enZybmpmYl5aV
    lJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1c
    W1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQj
    IiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYFBAMCAQAAIfkEAQAACQAsAAAAACgAKAAABJww
    yUmrvTjrzXH4YCiGRncFQKqubBociFmhba0GAjHIE23XqNyO5/uxaEKiEahKmopL18rJgUahgsJw
    Y11as9tM1zgKVaNoQOCc9rLbvzUXTn7TW3LN+J4X3219Hn9AdoMuhYaBJ4ZHiIOKFnt0kDOMK5QU
    knCYPZY3jn+cEpptogmkaaaoaKqeh3OurbGgfLSTVWW5uiA8vb6/PBEAOw==
    """

    _ICON_ADD_FOLDER = """
    R0lGODlhKAAoALMPAK+PVO7p4ZZ6RMOykbiaYduwZaCETcagW86qZ9y3dOG9d+zGf9HFrfLLg/XO
    hf///yH/C1hNUCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpy
    ZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0
    az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQw
    ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIv
    MjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4
    bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMu
    YWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94
    YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3No
    b3AgQ0MgMjAxNS41IChXaW5kb3dzKSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpENjlCRDk0
    NUIxMzcxMUU2QTY4Qjk0QjVFRDQzMkJGNyIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpENjlC
    RDk0NkIxMzcxMUU2QTY4Qjk0QjVFRDQzMkJGNyI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjpp
    bnN0YW5jZUlEPSJ4bXAuaWlkOkQ2OUJEOTQzQjEzNzExRTZBNjhCOTRCNUVENDMyQkY3IiBzdFJl
    Zjpkb2N1bWVudElEPSJ4bXAuZGlkOkQ2OUJEOTQ0QjEzNzExRTZBNjhCOTRCNUVENDMyQkY3Ii8+
    IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5k
    PSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/O
    zczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGwr66trKuqqainpqWko6KhoJ+enZybmpmYl5aV
    lJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1c
    W1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQj
    IiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYFBAMCAQAAIfkEAQAADwAsAAAAACgAKAAABNjw
    yUmrvTjrzbv/YIgJZGkKjKgJReu6iJGqF/vehTHQlo3DhpNwWKr4fsgkTmBUOp9MyvFJfUUn02r1
    KskqAcRwyfDw/g4GQsPBbrvf7QSh3EKIBQYFfL9H7GwHAHyDhG8EKTYEB4WMgwABdAUACI2VbwaQ
    NnmWnAtkkQJrnJVyXQUxo5Z+poGplYemk66Nj7EJs4yYpgILuISeWKi+g6VdrcN8q12KyHywXbLN
    cLVdm9KXkF2h127AWAbcbsXL4W3KXQii4c9dt+UOulh383fZPPf4+fr7NBEAOw==
    """

    _ICON_FAVICON = """
    R0lGODlhgACAAPcAAJDVZZjOdEiCI3i+TIvLYn62Wk2GKG6tRk2NJFyZNaXagpfRcXKxS5bOclmS
    Nk6JKEyEJ6zgiZ7ZeY/JaobCYWKmNqzgimGfOnWzTUuJInq3VKfggX3CUXS2SUN+H1GRKUaAIaPZ
    gKXbgYTCXIDFVG2vQq3iiqziiargh16bOIjFYZzXd1qeMJnQdXGyR16eNoC4XVmdLXayUJ3Zd2Od
    PUiEIo7Faqreh6XcgqLce0uKI43TYY/NZ02LJlaVLkiBJKnghaTefm6mSqXZgmatOJnXcZnVc0aC
    IIPAW4K5XlOOLVCKKkuIJEqGJEmEJGyqQ1yVN1SQLkqHI0mHI0WAID97G6jchqbbg0yGJ0qEJabf
    gnCvSEeBI6jehabcg6LYf1GKLKbchFCOKIfHX4zSX1eZLZbYbEqDJqPefUmCJWivO6nfhl2WOKfc
    hEuEJ0mDJKfchUeCIkyFJ0uEJkuFJlGLLKjdhafdhEmCJKbbhGqiRafdhavfiKvfiavgiUmDJane
    hqnfh0qDJVGLLUeBIkuFJ6vgiEmCJqjehqviiKrfiE6HKajdhqffg0iCJKbdg0eAIkeAI0uDJ6re
    iEqEJkyIJafehEqCJqvhiEyHJ5fVcVaYLVadKaLbfYfFX2CYO2+4QHy/UmWlPKDdeaDeeqTffm26
    PX67WF2eMovIZIrMYIzLZUqFJVaaK6PZf67ii3KtS2OrNYbFXVKXJ6fdg6begVOVKFSXKoC2XGyr
    Q1uhLJTOb5nRdleUMKjfhlGOKqbegpvVdqffgqDbeojHXoTAXqbcgne3TqTcgKPdflGJLJzcc1KL
    LandiJnZcKndh5PSa6vginm5UYbKW3q8UEuMI3nBSobGXofGXqjfhHi4TqrfiYzFZ2WdQLHlj67j
    jFuWNUyIJk6LJ0iFIKXfgEiGIYS+X6rhhqrghWmwPFaYLIDJUpXYa3CuSWGhOGSgPovSXkmFJFWO
    MJDRZlCPKFGPKZfWb4nLXprTdoG4XW+yRViaLqzhiVieK02HKKXbgiH/C1hNUCBEYXRhWE1QPD94
    cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1w
    bWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42
    LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQwICAgICAgICAiPiA8cmRmOlJERiB4
    bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8
    cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2Jl
    LmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEu
    MC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAv
    MS4wLyIgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOmI0YTU3ZWJmLTUxNzYtMjU0
    Ny1hMzhmLWVmMDkxYmM0OGM4YiIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDo1MzkxODY1Rjk5
    NTkxMUU2QjZDOEQ4RDI2QUU3QTFGNiIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo1MzkxODY1
    RTk5NTkxMUU2QjZDOEQ4RDI2QUU3QTFGNiIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3No
    b3AgQ0MgMjAxNS41IChXaW5kb3dzKSI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5j
    ZUlEPSJ4bXAuaWlkOmI0YTU3ZWJmLTUxNzYtMjU0Ny1hMzhmLWVmMDkxYmM0OGM4YiIgc3RSZWY6
    ZG9jdW1lbnRJRD0ieG1wLmRpZDpiNGE1N2ViZi01MTc2LTI1NDctYTM4Zi1lZjA5MWJjNDhjOGIi
    Lz4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBl
    bmQ9InIiPz4B//79/Pv6+fj39vX08/Lx8O/u7ezr6uno5+bl5OPi4eDf3t3c29rZ2NfW1dTT0tHQ
    z87NzMvKycjHxsXEw8LBwL++vby7urm4t7a1tLOysbCvrq2sq6qpqKempaSjoqGgn56dnJuamZiX
    lpWUk5KRkI+OjYyLiomIh4aFhIOCgYB/fn18e3p5eHd2dXRzcnFwb25tbGtqaWhnZmVkY2JhYF9e
    XVxbWllYV1ZVVFNSUVBPTk1MS0pJSEdGRURDQkFAPz49PDs6OTg3NjU0MzIxMC8uLSwrKikoJyYl
    JCMiISAfHh0cGxoZGBcWFRQTEhEQDw4NDAsKCQgHBgUEAwIBAAAh+QQAAAAAACwAAAAAgACAAAAI
    /wD/CRxIsKDBgwgTKlzIsKHDhxAjSpxIsaLFixgzatzIsaPHjyBDihxJsqTJkyhTqlzJsqXLlzBj
    ypxJs6bNmzhz6tzJs6fPn0CDCh1KtKjRo0iTKl3KtKnTp1CjSp1KtarVq1izat3KtavXr2DDdgyz
    p4tZs3bgXLl4BY6ds13Srv0J6AS/u3dPBBKBsA0ffkGCtQhAOAC+GcJOKJJ45caJDSsGF+a1gtyJ
    Pnl4PppQIJ9nzwVsdDF4xQIpFTBK2Kr0J0sWVh/6Mcg3BlOgh9s28EiCoV+P1ln+iOPkIh+xUhZ0
    XtGSqwqI58+rdDNB8I4vCS5S6KDyQ46/79/luP/5QQXBu2LZRie80oVWKBofuLsxAN6fgfFUql2Q
    caeLl5vLbcFFff7EoQc/A/mhQAe/OIGHdwRGKEccmbzQgCFzFWRFH/ewkMUPbkQooSNO+FAMP23Y
    FOCA9RmI4D+B8EADJFiIaON3WOCxBDa1ZEbQM8vIIMUc9N0oYiECaIBGijStSKCLXhgyAgJ4PGCk
    kZQwwQEQBPGxAAtH1HiljVgQok8pTMrkZIsHRnCKFJSMeeUc4aTChwgiKLKAOngUKaeIWAhwDApN
    aiHgk3p4g8QUYhKIxaOQNmrjH1EYwcgNC2ySBaCRPnolFj0QYMdMa4IXhxDzIFAIgQa8Ec8Dg9T/
    ISszSzjxhp8RUiHDNzPE8IOjArwaq6yD1PqGkW+80AiphrIInhv7xHAJgYeUk0IJO4SgbQhD2HNA
    AuOsKiIE9GiCgQAE4lEJDbnMM8S2CkCTCziE4FqfHEzIEo2azUoIIXhvoIJEMhbAYYwXCOPQBj/D
    nLIIHTbOccG/9kFyAQXn8AEHDgj/14YfnTCAQIgiRvLEBj6+VKqNdLxRQA78hJFQG6/YkImk9R37
    bAYMiICJQoygo8oHJBMoBwK7rBHTyhFiwUQxmOzB0BWJSBPHmG7Us84ad0ytyDRM2EgIN0rDxDSB
    b5jzs0N7SJCAzjbKoQMJhjzEXjuOiCjIAMua/92vjXEwcE6GDfGjTRP25nwAECk35AcPCFD8nRux
    IEM4S2d/J0gvRgASURhFKIEzeFj4IEGaDsExijtpSBiFK/+p/DerNWBAnUR2yAOxiFlQg8hEJghB
    SNPKfBG7S5nToUQRqD/0SAVxitjEAupF5AcsNTQNhvF+HxohHQn8PtEjoMwh4iEV5NC8Q30crj33
    sntP4BymdD2RJdZsGiEIBSRC0SQk0AHOsLC947Ukc1kgQPUiYgkS6I9AIMDFCf5Hgh4MsIDdc1Z9
    BNGCBUKkC2N4IHjk5ok+UMQKOxCD5AgIP+TNjnQ94IXUJgJCEX5HErMAQDNOSAYVOgqD8dNgeP9a
    sQL7SaSGETpDGcxgBR76sD4sNCDmXnhDXZyOIkgkkBKZ6MQVAtGF8gPPJYiQA5nRMIRJXGITJ2KF
    HnqxhQekoj/SkA40mPGIaNSiGrv4QzhOMYzfSYMa7IjFPNZni2uUSBufSLovxhGQcxzkHSOSxUPu
    kY1u7KMUV3I2QRLyjDb0ByL5CEVH/lGIkfwkHkM5SkwyEkem5KQcPTnJDxoSPK1UZCZL6UdZQpKW
    hWTlJXX5Sn9EMYMRAiYo08hFV75xkyrppCSDycxERmSRz0QmgZS5ymqSspG9jOYsp7lMPTaTmNkM
    YjLJ2U1zWhMi2NSkNuvDTUre8ju5vOYuwQn/zZRIU5X2FOY59VnMY6pzm+wMqDedKc+D0jOhthTo
    Ox8ST172EyX/rOVDKonLYRI0nWBEZT0julB0NjSk6wQoSd35TViG05/jVOlG7ylKj8Jzny696Eky
    Sk2WMtSi8wTPSGcq0ZYaM5bi/CVEiVrSj570kSJdqkM4ik+bUhSnR30pRmOq0anSNJ83LShSYapU
    mXq1qD/lZ1ADKdWGULWmAw0rSKGa0q669atWdUhF1epQobaVIW8F61XFqtWdcrWnlozrYOc6xQN4
    wDWQzQIIiGBWt16DEJF1TSRuwY6J6hUePcBDZt+wiMKa5ArA0IAD2MDa1jqgA8mwK0PusIrVYbaW
    tQ4QhTPgQBE4ACAFULgtG6DwiRDoFCV7WINyl6vcUVkkDMxlLiAuF5E8RJe5YsmudrfL3e5697vg
    Da94x0ve8pr3vOhNr3rXy972uve98I2vfOdL3/ra9774zS93AwIAOw==
    """

    _ICON_LOGO = """
    R0lGODlhbgHIALMPAO/q8bvgo0MMYfn89vP28qmXtYbBX1CKKtfS2tjnz+/x7o91n2tEgaXbguvr
    6////yH/C1hNUCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpy
    ZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0
    az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQw
    ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIv
    MjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4
    bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6
    Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtbG5zOnhtcD0iaHR0
    cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpEQjAy
    MDlEOUIxM0ExMUU2QjlFNUFFMTY1Njc5NTUxQSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpE
    QjAyMDlEOEIxM0ExMUU2QjlFNUFFMTY1Njc5NTUxQSIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQ
    aG90b3Nob3AgQ0MgMjAxNS41IChXaW5kb3dzKSI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjpp
    bnN0YW5jZUlEPSJ4bXAuaWlkOkU1OENDREFGOTk1NzExRTY4RDc1RENFMjcxRTlEMDM3IiBzdFJl
    Zjpkb2N1bWVudElEPSJ4bXAuZGlkOkU1OENDREIwOTk1NzExRTY4RDc1RENFMjcxRTlEMDM3Ii8+
    IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5k
    PSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/O
    zczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGwr66trKuqqainpqWko6KhoJ+enZybmpmYl5aV
    lJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1c
    W1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQj
    IiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYFBAMCAQAAIfkEAQAADwAsAAAAAG4ByAAABP/w
    yUmrvTjrLUf4TSg235ckxMCt2ECcZTCOQcLeeK7vfO//wKBwmBnMjseSIvUbKBIgpJRErFqv2Kx2
    y23JpmBSQKHCOb/hqa3Lbrvf8DgOnQYnyhtFtK6W+/+AgYI6dHxTAQQZBIWGSGuDkJGSk1uMjUl3
    FR6XaQqUn6ChohwJnGkBeHqmYZ6jrq+wg1AmNTF7jYgPpZwyMVCzH4mxw8TFfwMuL1B8Ncw1KCl4
    xtPU1YAuy6shNUzW3t/gcS6WaSjh5+jpW4uGqOrv8PE/u6zy9vf4GvRSrfn+//bINXgEsKDBcEaQ
    uDvIsCE1SwQdSpwoap+IfhQzaoSkAIm0jSD/Q74h4FGkyZNcOh75iLKlSx8kV76cSVOHyhksa+rc
    OSEmTp5Ag94ckTOoUZQ+iR5d+nKoiKJMo1JM+lSqVZBOQ0C9yhUgVa1dwzbM2mCr2LPwvpZFyzYf
    WbNt43pTC1euXWNv7/JExrev37+AAwseTLiwYcF0DytezLix48eQI0ueTHkyg8uYM2vezLmz58+g
    Q4vuvADJ6NOoU6tezbq169ewY8cWQLu27du4c+vezbu379+6GSABTry48ePIkytfzry58+fQo0sH
    LvzI9OvYs2vfzr279++/q88AT768+fPo06vnLX7E+vfw48ufT19AexH18+vfz79/+OH+BSjg/4DE
    MVDAgQUsgKCCBzKY4IIQNhjhgxJWSOGFDmaI4IYcdmghg0hs6KCHJJZo4okopqjiiiy26OKLMMYo
    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
    """

    _ICON_MATCH = """
    R0lGODlhKAAoALMPAPjmom6BlvT4/azO9o+68cejZsXb+MbN06Gditvm9ZzD87vDxbff/MLo/4Oc
    sv///yH/C1hNUCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpy
    ZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0
    az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQw
    ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIv
    MjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4
    bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMu
    YWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94
    YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3No
    b3AgQ0MgMjAxNS41IChXaW5kb3dzKSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpDQTk5NzRF
    Q0IxMzcxMUU2QjI4QzgyQUE5QkI4NTFBNiIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpDQTk5
    NzRFREIxMzcxMUU2QjI4QzgyQUE5QkI4NTFBNiI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjpp
    bnN0YW5jZUlEPSJ4bXAuaWlkOkNBOTk3NEVBQjEzNzExRTZCMjhDODJBQTlCQjg1MUE2IiBzdFJl
    Zjpkb2N1bWVudElEPSJ4bXAuZGlkOkNBOTk3NEVCQjEzNzExRTZCMjhDODJBQTlCQjg1MUE2Ii8+
    IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5k
    PSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/O
    zczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGwr66trKuqqainpqWko6KhoJ+enZybmpmYl5aV
    lJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1c
    W1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQj
    IiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYFBAMCAQAAIfkEAQAADwAsAAAAACgAKAAABP/w
    yUmrvTjrLQURXHgJBvgkX5eYIqcMoEEYjzAorSi/BEPcs1wooWAMGg2GUpEQYgSJ1eCIrDam0JJz
    4iG8rOABwcvaCr7IRaEQhm0rnnQBsLam3hSDoqEG+OtICjR4Jwo9B3N+f1U+A01vQH2KdAdVhi+E
    D3STlFVYmQ+InAWVnoOEm5MFC4wKhmVOCYmKq0pKBAkyA3gHCKMLrmKCHbAtCQEBvn8AMk0op2/H
    AQ7Jmw8GuxID0E4H0w7gyQegFsfg58nkFd7n4QvqFOztAe/wEvLo9fb47iN33d/yYZDBTQQ/avoo
    kOgxo5iGgwHGXRjDIMmYFhATVkhww4eWEBA6JWrwiDFgPw4eHF4ISSjlOpPURL4hGA8mvZYyPJqw
    qdEJRYsEJFBDJzNax4YdhkaER1NhTHsu7YmIAAA7
    """

    _ICON_NEXT = """
    R0lGODlhKAAoALMPAHGphW6ng63NubPRv6nLtrrgvV6cdrDZtbTSv7XSwLLat2+ohLDYta/Ou6/Y
    tP///yH/C1hNUCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpy
    ZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0
    az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQw
    ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIv
    MjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4
    bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMu
    YWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94
    YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3No
    b3AgQ0MgMjAxNS41IChXaW5kb3dzKSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpCQzQ0NkM4
    OEIxMzcxMUU2QTk5NkZENjM4QUNGNjlBMiIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpCQzQ0
    NkM4OUIxMzcxMUU2QTk5NkZENjM4QUNGNjlBMiI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjpp
    bnN0YW5jZUlEPSJ4bXAuaWlkOkJDNDQ2Qzg2QjEzNzExRTZBOTk2RkQ2MzhBQ0Y2OUEyIiBzdFJl
    Zjpkb2N1bWVudElEPSJ4bXAuZGlkOkJDNDQ2Qzg3QjEzNzExRTZBOTk2RkQ2MzhBQ0Y2OUEyIi8+
    IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5k
    PSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/O
    zczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGwr66trKuqqainpqWko6KhoJ+enZybmpmYl5aV
    lJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1c
    W1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQj
    IiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYFBAMCAQAAIfkEAQAADwAsAAAAACgAKAAABJjw
    yUmrvTjrzbs1YOiNlVGchUGuj4mq7OiecNzNqe3hta7xPg4w+EPliJkh8qJclow956QplVCrV2nW
    uV12kV9iODj2lXVnWzq21ghCcF4c1IgJAAqjXq8ACHQJCwd7ewcLCUEJAYOEJwcBiEQIi42PkUiT
    jEaPCFWZmwGdVQ8DlAUMoaMTpQwOAQOqFAQLCwSxFQJ/t7uqEQA7
    """

    _ICON_PREVIOUS = """
    R0lGODlhKAAoALMPALrUxLHPvW+ohLrgvV6cdrLat7Pbt63NuXGphXCpha7NunCphK/OurLQvV+c
    d////yH/C1hNUCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpy
    ZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0
    az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQw
    ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIv
    MjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4
    bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMu
    YWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94
    YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3No
    b3AgQ0MgMjAxNS41IChXaW5kb3dzKSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpCNjZBOEQ4
    RUIxMzcxMUU2QjM4OEZEQThGRkMyRjBBMCIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpCNjZB
    OEQ4RkIxMzcxMUU2QjM4OEZEQThGRkMyRjBBMCI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjpp
    bnN0YW5jZUlEPSJ4bXAuaWlkOkI2NkE4RDhDQjEzNzExRTZCMzg4RkRBOEZGQzJGMEEwIiBzdFJl
    Zjpkb2N1bWVudElEPSJ4bXAuZGlkOkI2NkE4RDhEQjEzNzExRTZCMzg4RkRBOEZGQzJGMEEwIi8+
    IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5k
    PSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/O
    zczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGwr66trKuqqainpqWko6KhoJ+enZybmpmYl5aV
    lJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1c
    W1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQj
    IiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYFBAMCAQAAIfkEAQAADwAsAAAAACgAKAAABJbw
    yUmrvTjrzTtujSd+ghCMqHQkhpEcqbgaw+DC8TbXtYEoucwBQePVCr+gRYEoGI1IoFKiWDif0AVj
    yrBisQVtkNH8fgumGMBBaLsJxrfbAZhO4DyCXYOv6fcYfQN/gBaChIUUh4mGcYwVi493jpISkZWX
    kpmPm4ydiZ+FoYCje6V2p1OpSqtBrTmvMbEpsyhyiJW5iREAOw==
    """

    _ICON_REMOVE = """
    R0lGODlhKAAoALMPAPePj81SUuJvb/iYmPTKyvHQ0P7t7dVsbHiLnP7y8vbi4uaDg7lVWfjn5///
    /////yH/C1hNUCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpy
    ZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0
    az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQw
    ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIv
    MjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4
    bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMu
    YWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94
    YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3No
    b3AgQ0MgMjAxNS41IChXaW5kb3dzKSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpBODE5RjEx
    NkIxMzcxMUU2OTBGQkIzMDY3QjY4ODYzOCIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpBODE5
    RjExN0IxMzcxMUU2OTBGQkIzMDY3QjY4ODYzOCI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjpp
    bnN0YW5jZUlEPSJ4bXAuaWlkOkE4MTlGMTE0QjEzNzExRTY5MEZCQjMwNjdCNjg4NjM4IiBzdFJl
    Zjpkb2N1bWVudElEPSJ4bXAuZGlkOkE4MTlGMTE1QjEzNzExRTY5MEZCQjMwNjdCNjg4NjM4Ii8+
    IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5k
    PSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/O
    zczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGwr66trKuqqainpqWko6KhoJ+enZybmpmYl5aV
    lJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1c
    W1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQj
    IiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYFBAMCAQAAIfkEAQAADwAsAAAAACgAKAAABOHw
    yUmrvTjrzbv/YCiOZGmeaKqubOu+KSLPdG3fuCwhTu//wKBwiNgNj8hj8cFLOp3L5nMqjFKvQCt2
    q91eu94pOOwoLALowILgG28Vh4BgAVgsBIGDwuG+FuQAgYKBeAV9UwqAg4tnUTmPMgwCggODlYQM
    JwQBggQJlwMJBIIBBSZ3gQMGDgYDqqyXcyZqlKsJCbCCZ7OLr7mDAbyWuA6fi8EltKm4BraXdcgk
    qACvrdWxCyZ/na2pDaOBpScHk4upggIHKIl05roBCil/5eaFKw1xc4F3eQ0uBGfSLDBFIQIAOw==
    """

    _ICON_RENAME = """
    R0lGODlhKAAoALMPAP///9zV8vnon72iXOSKjqKXjMPo/ot2ocjR23mLnGd5jz1FTsVbXtnClbu9
    1P///yH/C1hNUCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpy
    ZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0
    az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQw
    ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIv
    MjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4
    bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMu
    YWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94
    YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3No
    b3AgQ0MgMjAxNS41IChXaW5kb3dzKSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo4OTBCODFG
    M0IxRjAxMUU2ODNCQ0MyRTlENjQxMEZDMSIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDo4OTBC
    ODFGNEIxRjAxMUU2ODNCQ0MyRTlENjQxMEZDMSI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjpp
    bnN0YW5jZUlEPSJ4bXAuaWlkOjg5MEI4MUYxQjFGMDExRTY4M0JDQzJFOUQ2NDEwRkMxIiBzdFJl
    Zjpkb2N1bWVudElEPSJ4bXAuZGlkOjg5MEI4MUYyQjFGMDExRTY4M0JDQzJFOUQ2NDEwRkMxIi8+
    IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5k
    PSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/O
    zczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGwr66trKuqqainpqWko6KhoJ+enZybmpmYl5aV
    lJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1c
    W1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQj
    IiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYFBAMCAQAAIfkEAQAADwAsAAAAACgAKAAABP/w
    yUmrvTjrzen5YHgoZGmeyhFsauC6oOIgdG3bTrpm7RvEt+BNgVDxfLAPUUgr1RSB4s7SewGZCGfT
    Jb1UkyNslvR8OYyV708p1mZ9XQ9yHca6oXC0RH1l3ucEDAwEe3N9YmU+BYOBhUgxM4g0Dgk+lAkE
    mY6WMSieJA4vBQkGAZiED2pzq6wuDQmhBggJDJutt3MNAwIJCKUJBba4w7oCxrC9E6rDq8XGx8HK
    zMS7zwIDDQdyLgnd3t/g4QXVz9g/26YA6uvs7ezO5Q0w6Anu9u3wxgMFVvT3//mu8eonjds/ewPI
    6RMAoNK8gunUGZhIseLEhNauNVDn8BzEegdx1wXAWI4hR4KbQIYEkJAkNnYdtX1cqQ6bAF0vYaJM
    9UKlRYsKsOEcQHFdTH8rFywYwGAAAntHZ4YsoFTBwagpVyoosBIrT4MSf4r9aXRnD5U0r5rtmbbr
    WrBt/3k9G1ftwz0gwundqzdEh7+AAwu+EAEAOw==
    """

    def __init__(self):
        self.__store = {
            'add_file': PhotoImage(data=self._ICON_ADD_FILE),
            'add_folder': PhotoImage(data=self._ICON_ADD_FOLDER),
            'favicon': PhotoImage(data=self._ICON_FAVICON),
            'logo': PhotoImage(data=self._ICON_LOGO),
            'match': PhotoImage(data=self._ICON_MATCH),
            'next': PhotoImage(data=self._ICON_NEXT),
            'previous': PhotoImage(data=self._ICON_PREVIOUS),
            'remove': PhotoImage(data=self._ICON_REMOVE),
            'rename': PhotoImage(data=self._ICON_RENAME)
        }
