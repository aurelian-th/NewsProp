from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataSource:
    name: str
    url: str
    note: str


@dataclass(frozen=True)
class MoldovaCalibration:
    # World Bank API: https://api.worldbank.org/v2/country/MDA/indicator/SP.POP.TOTL?format=json
    population_total_2024: int = 2402306

    # World Bank API: https://api.worldbank.org/v2/country/MDA/indicator/SP.URB.TOTL.IN.ZS?format=json
    urban_share_2024: float = 0.4351647186

    # World Bank API: https://api.worldbank.org/v2/country/MDA/indicator/IT.NET.USER.ZS?format=json
    internet_users_share_2023: float = 0.802126

    # Derived from World Bank age structure indicators for Moldova (2024).
    # 15-64 = 63.9998%, 65+ = 16.2115%. Model is 18-80 only, so we allocate
    # adults into a working-age and senior mixture close to observed structure.
    age_share_65_80: float = 0.213
    age_share_18_64: float = 0.787

    # Channel priors reflect 2023-2025 Moldova studies:
    # - social networks / internet: major source for many users
    # - TV: still high-trust and strong second channel
    # - mouth: interpersonal transmission residual
    channel_target_social: float = 0.50
    channel_target_tv: float = 0.34
    channel_target_mouth: float = 0.16


SOURCES: tuple[DataSource, ...] = (
    DataSource(
        name="NetworkX barabasi_albert_graph",
        url="https://networkx.org/documentation/stable/reference/generated/networkx.generators.random_graphs.barabasi_albert_graph.html",
        note="Scale-free graph generation specification and constraints.",
    ),
    DataSource(
        name="NetworkX betweenness_centrality",
        url="https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.centrality.betweenness_centrality.html",
        note="Node betweenness centrality definition and options.",
    ),
    DataSource(
        name="NetworkX eigenvector_centrality",
        url="https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.centrality.eigenvector_centrality.html",
        note="Eigenvector centrality behavior and convergence constraints.",
    ),
    DataSource(
        name="World Bank SP.POP.1564.TO.ZS",
        url="https://api.worldbank.org/v2/country/MDA/indicator/SP.POP.1564.TO.ZS?format=json",
        note="Moldova age 15-64 share.",
    ),
    DataSource(
        name="World Bank SP.POP.65UP.TO.ZS",
        url="https://api.worldbank.org/v2/country/MDA/indicator/SP.POP.65UP.TO.ZS?format=json",
        note="Moldova age 65+ share.",
    ),
    DataSource(
        name="World Bank IT.NET.USER.ZS",
        url="https://api.worldbank.org/v2/country/MDA/indicator/IT.NET.USER.ZS?format=json",
        note="Moldova internet usage share.",
    ),
    DataSource(
        name="World Bank SP.URB.TOTL.IN.ZS",
        url="https://api.worldbank.org/v2/country/MDA/indicator/SP.URB.TOTL.IN.ZS?format=json",
        note="Moldova urban share.",
    ),
    DataSource(
        name="IJC Media Audience Study 2025",
        url="https://cji.md/en/media-audience-study-launched-by-the-ijc-social-networks-have-become-the-main-source-of-information-for-media-consumers-in-the-republic-of-moldova/",
        note="Social networks lead as information source, TV high trust, 28.6% trust none.",
    ),
    DataSource(
        name="MOM Moldova Media Consumption",
        url="https://moldova.mom-gmr.org/en/context/media-consumption",
        note="Internet and TV channel prevalence and trust context in Moldova.",
    ),
    DataSource(
        name="MOM Moldova Social Media",
        url="https://moldova.mom-gmr.org/en/media/social-media/",
        note="Platform-level social media usage context in Moldova.",
    ),
)


def default_calibration() -> MoldovaCalibration:
    return MoldovaCalibration()
