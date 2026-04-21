from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    id: str
    description: str
    user_turns: list[str]
    must_collect: list[str]
    should_call_end_call: bool
    end_call_turn_index: int | None = None


SCENARIOS = [
    Scenario(
        id="unknown_caller_full_flow",
        description="Unknown caller provides reason and name, then closes call.",
        user_turns=[
            "Dzień dobry, proszę przekazać że oddzwoni.",
            "Chodzi o fakturę za marzec.",
            "Nazywam się Marta.",
            "Nie, to wszystko dziękuję.",
        ],
        must_collect=["faktur", "marta"],
        should_call_end_call=True,
        end_call_turn_index=3,
    ),
    Scenario(
        id="silence_fallback",
        description="User is silent then provides a valid reason.",
        user_turns=[
            "[cisza]",
            "Proszę przekazać, że spotkanie jutro o 15.",
            "Nie, dziękuję.",
        ],
        must_collect=["spotkanie", "15"],
        should_call_end_call=True,
        end_call_turn_index=2,
    ),
    Scenario(
        id="short_info_no_premature_end",
        description="A short exchange where assistant should not end too early.",
        user_turns=[
            "Cześć, chciałem zostawić wiadomość.",
            "Nie podam więcej szczegółów.",
        ],
        must_collect=[],
        should_call_end_call=False,
        end_call_turn_index=None,
    ),
    Scenario(
        id="insurance_sales_call",
        description="Caller from insurance offers policy and closes politely.",
        user_turns=[
            "Dzwonię z ubezpieczenia, mam ofertę dla Sergiusza.",
            "Chodzi o polisę na mieszkanie, taniej o 20 procent.",
            "Nazywam się Tomasz, proszę o kontakt jutro.",
            "Dziękuję, to wszystko.",
        ],
        must_collect=["ubezpieczenia", "polis", "tomasz", "jutro"],
        should_call_end_call=True,
        end_call_turn_index=3,
    ),
    Scenario(
        id="listing_inquiry_call",
        description="Caller asks about listing and leaves callback details.",
        user_turns=[
            "Dzwonię w sprawie ogłoszenia mieszkania.",
            "Czy ogłoszenie jest nadal aktualne?",
            "Proszę przekazać, że oddzwonię po 18, Asia.",
            "Dziękuję, do usłyszenia.",
        ],
        must_collect=["ogłoszenia", "aktualne", "asia", "18"],
        should_call_end_call=True,
        end_call_turn_index=3,
    ),
    Scenario(
        id="known_caller_quick_close",
        description="Known caller leaves a short message and ends quickly.",
        user_turns=[
            "Cześć, tu Michał. Powiedz Sergiuszowi, że dojadę później.",
            "Będę około 19, dzięki.",
            "Nie, to wszystko.",
        ],
        must_collect=["michał", "19", "później"],
        should_call_end_call=True,
        end_call_turn_index=2,
    ),
]
