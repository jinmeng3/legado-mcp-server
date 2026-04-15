from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LegadoBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# noinspection DuplicatedCode
class CatalogRuleBase(LegadoBaseModel):
    bookList: str | None = None
    name: str | None = None
    author: str | None = None
    intro: str | None = None
    kind: str | None = None
    lastChapter: str | None = None
    updateTime: str | None = None
    bookUrl: str | None = None
    coverUrl: str | None = None
    wordCount: str | None = None


class SearchRule(CatalogRuleBase):
    checkKeyWord: str | None = None


class ExploreRule(CatalogRuleBase):
    pass


class BookInfoRule(LegadoBaseModel):
    init: str | None = None
    name: str | None = None
    author: str | None = None
    intro: str | None = None
    kind: str | None = None
    lastChapter: str | None = None
    updateTime: str | None = None
    coverUrl: str | None = None
    tocUrl: str | None = None
    wordCount: str | None = None
    canReName: str | None = None
    downloadUrls: str | None = None


# noinspection DuplicatedCode
class TocRule(LegadoBaseModel):
    preUpdateJs: str | None = None
    chapterList: str | None = None
    chapterName: str | None = None
    chapterUrl: str | None = None
    formatJs: str | None = None
    isVolume: str | None = None
    isVip: str | None = None
    isPay: str | None = None
    updateTime: str | None = None
    nextTocUrl: str | None = None


class ContentRule(LegadoBaseModel):
    content: str | None = None
    subContent: str | None = None
    title: str | None = None
    nextContentUrl: str | None = None
    webJs: str | None = None
    sourceRegex: str | None = None
    replaceRegex: str | None = None
    imageStyle: str | None = None
    imageDecode: str | None = None
    payAction: str | None = None
    callBackJs: str | None = None


class BookReadConfig(LegadoBaseModel):
    reverseToc: bool = False
    pageAnim: int | None = None
    reSegment: bool = False
    imageStyle: str | None = None
    useReplaceRule: bool | None = None
    delTag: int = 0
    ttsEngine: str | None = None
    splitLongChapter: bool = True
    readSimulating: bool = False
    startDate: str | None = None
    startChapter: int | None = None
    dailyChapters: int = 3
    openCredits: int = 0
    closeCredits: int = 0
    playMode: int = 0
    playSpeed: float = 1.0


class BookSource(LegadoBaseModel):
    bookSourceUrl: str = ""
    bookSourceName: str = ""
    bookSourceGroup: str | None = None
    bookSourceType: int = 0
    bookUrlPattern: str | None = None
    customOrder: int = 0
    enabled: bool = True
    enabledExplore: bool = True
    jsLib: str | None = None
    enabledCookieJar: bool | None = True
    concurrentRate: str | None = None
    header: str | None = None
    loginUrl: str | None = None
    loginUi: str | None = None
    loginCheckJs: str | None = None
    coverDecodeJs: str | None = None
    bookSourceComment: str | None = None
    variableComment: str | None = None
    lastUpdateTime: int = 0
    respondTime: int = 180000
    weight: int = 0
    exploreUrl: str | None = None
    exploreScreen: str | None = None
    ruleExplore: ExploreRule | None = None
    searchUrl: str | None = None
    ruleSearch: SearchRule | None = None
    ruleBookInfo: BookInfoRule | None = None
    ruleToc: TocRule | None = None
    ruleContent: ContentRule | None = None
    ruleReview: dict[str, Any] | None = None
    eventListener: bool = False
    customButton: bool = False


class RssSource(LegadoBaseModel):
    sourceUrl: str = ""
    sourceName: str = ""
    sourceIcon: str = ""
    sourceGroup: str | None = None
    sourceComment: str | None = None
    enabled: bool = True
    variableComment: str | None = None
    jsLib: str | None = None
    enabledCookieJar: bool | None = True
    concurrentRate: str | None = None
    header: str | None = None
    loginUrl: str | None = None
    loginUi: str | None = None
    loginCheckJs: str | None = None
    coverDecodeJs: str | None = None
    sortUrl: str | None = None
    singleUrl: bool = False
    articleStyle: int = 0
    ruleArticles: str | None = None
    ruleNextPage: str | None = None
    ruleTitle: str | None = None
    rulePubDate: str | None = None
    ruleDescription: str | None = None
    ruleImage: str | None = None
    ruleLink: str | None = None
    ruleContent: str | None = None
    contentWhitelist: str | None = None
    contentBlacklist: str | None = None
    shouldOverrideUrlLoading: str | None = None
    style: str | None = None
    enableJs: bool = True
    loadWithBaseUrl: bool = True
    injectJs: str | None = None
    preloadJs: str | None = None
    startHtml: str | None = None
    startStyle: str | None = None
    startJs: str | None = None
    showWebLog: bool = False
    lastUpdateTime: int = 0
    customOrder: int = 0
    type: int = 0
    preload: bool = False
    cacheFirst: bool = False
    searchUrl: str | None = None


class ReplaceRule(LegadoBaseModel):
    id: int | None = None
    name: str = ""
    group: str | None = None
    pattern: str = ""
    replacement: str = ""
    scope: str | None = None
    scopeTitle: bool = False
    scopeContent: bool = True
    excludeScope: str | None = None
    isEnabled: bool = True
    isRegex: bool = True
    timeoutMillisecond: int = 3000
    order: int = Field(default=-(2**31))


class Book(LegadoBaseModel):
    bookUrl: str = ""
    tocUrl: str = ""
    origin: str = "loc_book"
    originName: str = ""
    name: str = ""
    author: str = ""
    kind: str | None = None
    customTag: str | None = None
    coverUrl: str | None = None
    customCoverUrl: str | None = None
    intro: str | None = None
    customIntro: str | None = None
    charset: str | None = None
    type: int = 0
    group: int = 0
    latestChapterTitle: str | None = None
    latestChapterTime: int = 0
    lastCheckTime: int = 0
    lastCheckCount: int = 0
    totalChapterNum: int = 0
    durChapterTitle: str | None = None
    durChapterIndex: int = 0
    durVolumeIndex: int = 0
    chapterInVolumeIndex: int = 0
    durChapterPos: int = 0
    durChapterTime: int = 0
    wordCount: str | None = None
    canUpdate: bool = True
    order: int = 0
    originOrder: int = 0
    variable: str | None = None
    readConfig: BookReadConfig | None = None
    syncTime: int = 0


class BookProgress(LegadoBaseModel):
    name: str
    author: str
    durChapterIndex: int
    durChapterPos: int
    durChapterTime: int
    durChapterTitle: str | None = None


class BookChapter(LegadoBaseModel):
    url: str = ""
    title: str = ""
    isVolume: bool = False
    baseUrl: str = ""
    bookUrl: str = ""
    index: int = 0
    isVip: bool = False
    isPay: bool = False
    resourceUrl: str | None = None
    tag: str | None = None
    wordCount: str | None = None
    start: int | None = None
    end: int | None = None
    startFragmentId: str | None = None
    endFragmentId: str | None = None
    variable: str | None = None
    imgUrl: str | None = None


class SearchBook(LegadoBaseModel):
    bookUrl: str = ""
    origin: str = ""
    originName: str = ""
    type: int = 0
    name: str = ""
    author: str = ""
    kind: str | None = None
    coverUrl: str | None = None
    intro: str | None = None
    wordCount: str | None = None
    latestChapterTitle: str | None = None
    tocUrl: str = ""
    time: int = 0
    variable: str | None = None
    originOrder: int = 0
    chapterWordCountText: str | None = None
    chapterWordCount: int = -1
    respondTime: int = -1
