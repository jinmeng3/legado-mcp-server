# Legado Web 服务接口文档

本文档基于 Legado 当前源码整理，不以旧版 `api.md` 为事实来源。重点覆盖 Legado Web HTTP / WebSocket 接口、请求参数、响应结构、数据模型，以及对 MCP 服务开发有影响的兼容性细节。

## 1. 服务概览

### 1.1 入口与端口

- HTTP 服务入口：`app/src/main/java/io/legado/app/web/HttpServer.kt`
- WebSocket 服务入口：`app/src/main/java/io/legado/app/web/WebSocketServer.kt`
- 服务管理：`app/src/main/java/io/legado/app/service/WebService.kt`
- 默认 HTTP 端口：`1122`
- WebSocket 端口：`HTTP 端口 + 1`，默认 `1123`

源码依据：

- `WebService.upWebServer()` 中创建 `HttpServer(port)` 与 `WebSocketServer(port + 1)`。
- `WebService.getPort()` 中默认端口为 `1122`。

### 1.2 HTTP 统一返回格式

大多数 HTTP JSON 接口返回 `ReturnData`：

```json
{
  "isSuccess": true,
  "errorMsg": "",
  "data": {}
}
```

字段说明：

| 字段 | 类型 | 必有 | 默认值 | 实际语义 |
| --- | --- | --- | --- | --- |
| `isSuccess` | `boolean` | 是 | `false` | Legado 控制器是否显式调用了 `setData()` |
| `errorMsg` | `string` | 是 | `"未知错误,请联系开发者!"` | 失败信息；少数接口成功时也可能保留默认值 |
| `data` | `any` | 否 | `null` | 实际返回数据 |

源码依据：

- `app/src/main/java/io/legado/app/api/ReturnData.kt`

### 1.3 重要例外

- `GET /cover`、`GET /image` 直接返回 `image/png` 二进制，不返回 `ReturnData`。
- 未命中的路径会回落到静态 Web 资源。
- 运行期异常可能直接返回纯文本 `e.message`，不是 JSON。
- `GET /getReplaceRules` 的 `data` 字段是一个 JSON 字符串，不是 JSON 数组。
- `POST /saveReplaceRule`、`POST /deleteReplaceRule` 成功时可能仍返回默认的 `ReturnData` 初始值，属于上游非标准行为。

源码依据：

- `HttpServer.serve()` 的响应分支与异常分支。
- `ReplaceRuleController.allRules()`、`saveRule()`、`delete()`。

### 1.4 与旧 `api.md` 的差异

- 旧文档里 `rssSourceDebug` 写了 `key`，但当前实现只消费 `tag`。
- 旧文档把 `saveReplaceRule` / `deleteReplaceRule` 写成数组输入，源码实际是单个 `ReplaceRule`。
- 旧文档未列出 `/refreshToc`、`/addLocalBook`、`/saveReadConfig`、`/getReadConfig`。
- 旧文档没有说明 `getReplaceRules` 返回的是“字符串化数组”。

## 2. HTTP 接口清单

统一说明：

- 地址示例中的 `127.0.0.1:1122` 请按 Legado 实际 HTTP 端口替换。
- `POST` 的 JSON 请求体均为原始 JSON 字符串。

---

### 2.1 书源接口

#### `POST /saveBookSource`

- 作用：插入或覆盖单个书源
- 请求体：`BookSource`
- 必填字段：`bookSourceUrl`、`bookSourceName`
- 成功响应：

```json
{
  "isSuccess": true,
  "errorMsg": "",
  "data": ""
}
```

- 失败条件：
  - 请求体为空
  - JSON 解析失败
  - 名称或 URL 为空

源码依据：

- `app/src/main/java/io/legado/app/api/controller/BookSourceController.kt`

#### `POST /saveBookSources`

- 作用：批量插入书源
- 请求体：`BookSource[]`
- 过滤逻辑：会跳过 `bookSourceName` 或 `bookSourceUrl` 为空的条目
- 成功响应：`data` 为实际插入的 `BookSource[]`

#### `POST /deleteBookSources`

- 作用：批量删除书源
- 请求体：`BookSource[]`
- 成功响应：

```json
{
  "isSuccess": true,
  "errorMsg": "",
  "data": "已执行"
}
```

#### `GET /getBookSource?url=<bookSourceUrl>`

- 作用：按书源 URL 获取单个书源
- 查询参数：

| 参数 | 类型 | 必填 | 实际语义 |
| --- | --- | --- | --- |
| `url` | `string` | 是 | `BookSource.bookSourceUrl` |

- 成功响应：`data = BookSource`

#### `GET /getBookSources`

- 作用：获取全部书源
- 成功响应：`data = BookSource[]`
- 注意：为空时返回失败，错误信息为“设备源列表为空”

---

### 2.2 RSS 源接口

#### `POST /saveRssSource`

- 作用：插入或覆盖单个 RSS 源
- 请求体：`RssSource`
- 必填字段：`sourceUrl`、`sourceName`

#### `POST /saveRssSources`

- 作用：批量插入 RSS 源
- 请求体：`RssSource[]`
- 响应：`data = 实际插入的 RssSource[]`

#### `POST /deleteRssSources`

- 作用：批量删除 RSS 源
- 请求体：`RssSource[]`

#### `GET /getRssSource?url=<sourceUrl>`

- 作用：按 URL 获取单个 RSS 源
- 查询参数：`url = RssSource.sourceUrl`

#### `GET /getRssSources`

- 作用：获取全部 RSS 源
- 注意：为空时返回失败，错误信息为“源列表为空”

源码依据：

- `app/src/main/java/io/legado/app/api/controller/RssSourceController.kt`

---

### 2.3 替换规则接口

#### `GET /getReplaceRules`

- 作用：获取全部替换规则
- 成功响应的真实结构：

```json
{
  "isSuccess": true,
  "errorMsg": "",
  "data": "[{\"id\":1,\"name\":\"...\"}]"
}
```

- 注意：`data` 是字符串，内容才是 `ReplaceRule[]` 的 JSON。

#### `POST /saveReplaceRule`

- 作用：插入或覆盖单个替换规则
- 请求体：`ReplaceRule`
- 特殊行为：
  - `order == Int.MIN_VALUE` 时，会自动设置为 `maxOrder + 1`
  - 成功时控制器没有调用 `setData()`，可能返回默认 `ReturnData`

#### `POST /deleteReplaceRule`

- 作用：删除单个替换规则
- 请求体：`ReplaceRule`
- 特殊行为：成功时也可能返回默认 `ReturnData`

#### `POST /testReplaceRule`

- 作用：测试替换规则
- 请求体：

```json
{
  "rule": {},
  "text": "待替换文本"
}
```

- `rule` 可以是对象，也可以是 JSON 字符串
- 成功响应：`data = 替换后的文本`

源码依据：

- `app/src/main/java/io/legado/app/api/controller/ReplaceRuleController.kt`

---

### 2.4 图书接口

#### `POST /saveBook`

- 作用：保存图书到书架
- 请求体：`Book`
- 成功响应：`data = ""`

#### `POST /deleteBook`

- 作用：从书架删除图书
- 请求体：`Book`

#### `GET /getBookshelf`

- 作用：获取书架全部图书
- 成功响应：`data = Book[]`
- 排序依赖 `AppConfig.bookshelfSort`
- 为空时返回失败，错误信息为“还没有添加小说”

#### `GET /refreshToc?url=<bookUrl>`

- 作用：强制刷新目录
- 查询参数：

| 参数 | 类型 | 必填 | 实际语义 |
| --- | --- | --- | --- |
| `url` | `string` | 是 | `Book.bookUrl` |

- 成功响应：`data = BookChapter[]`
- 特殊行为：
  - 本地图书走 `LocalBook.getChapterList`
  - 网络图书先查书源，再走 `WebBook.getBookInfoAwait` / `getChapterListAwait`

#### `GET /getChapterList?url=<bookUrl>`

- 作用：获取目录
- 特殊行为：如果数据库里没有目录，会自动转调 `/refreshToc`

#### `GET /getBookContent?url=<bookUrl>&index=<chapterIndex>`

- 作用：获取正文内容
- 查询参数：

| 参数 | 类型 | 必填 | 默认值 | 实际语义 |
| --- | --- | --- | --- | --- |
| `url` | `string` | 是 | - | `Book.bookUrl` |
| `index` | `integer` | 是 | - | `BookChapter.index` |

- 成功响应：`data = string`
- 特殊行为：
  - 会最多等待 30 秒，轮询章节记录是否已存在
  - 若本地缓存正文存在，则直接读取再做内容处理
  - 若不存在，则走书源正文抓取逻辑

#### `POST /saveBookProgress`

- 作用：保存阅读进度
- 请求体：`BookProgress`
- 特殊行为：按 `name + author` 查书，不按 `bookUrl`

#### `POST /addLocalBook`

- 作用：上传本地图书文件
- 请求类型：`multipart/form-data`
- 表单字段：

| 字段 | 类型 | 必填 | 实际语义 |
| --- | --- | --- | --- |
| `fileName` | `string` | 是 | 文件名 |
| `fileData` | `binary` | 是 | 上传文件内容 |

- 成功响应：`data = true`

源码依据：

- `app/src/main/java/io/legado/app/api/controller/BookController.kt`
- `app/src/main/assets/web/uploadBook/js/html5_fun.js`

---

### 2.5 Web 阅读配置接口

#### `POST /saveReadConfig`

- 作用：保存 Web 阅读界面配置
- 请求体：任意 JSON 字符串
- 特殊行为：
  - 有内容时直接原样缓存
  - 无内容时删除缓存键

#### `GET /getReadConfig`

- 作用：读取 Web 阅读界面配置
- 成功响应：`data = string`
- 注意：返回的是之前保存的原始 JSON 字符串，不会再解析成对象

---

### 2.6 图片接口

#### `GET /cover?path=<coverPath>`

- 作用：获取封面图片
- 返回类型：`image/png`
- 查询参数：

| 参数 | 类型 | 必填 | 实际语义 |
| --- | --- | --- | --- |
| `path` | `string` | 否 | 图书封面路径或 URL |

#### `GET /image?url=<bookUrl>&path=<imgUrl>&width=<width>`

- 作用：获取正文图片
- 返回类型：`image/png`
- 查询参数：

| 参数 | 类型 | 必填 | 默认值 | 实际语义 |
| --- | --- | --- | --- | --- |
| `url` | `string` | 是 | - | `Book.bookUrl` |
| `path` | `string` | 是 | - | 正文图片 URL |
| `width` | `integer` | 否 | `640` | 目标宽度 |

## 3. WebSocket 接口清单

统一说明：

- 地址示例默认端口 `1123`
- 当前实现会每 30 秒发送一次 `ping`
- 连接关闭条件通常是：
  - 调试流程结束
  - 发生错误
  - 参数校验失败

---

### 3.1 `ws://127.0.0.1:1123/bookSourceDebug`

- 作用：书源调试
- 首条消息格式：

```json
{
  "tag": "书源URL",
  "key": "调试关键字"
}
```

- 参数说明：

| 字段 | 类型 | 必填 | 实际语义 |
| --- | --- | --- | --- |
| `tag` | `string` | 是 | `BookSource.bookSourceUrl`，不是书源名称 |
| `key` | `string` | 是 | 调试模式输入值 |

- 服务端推送格式：纯文本日志，每条消息就是一段文本
- 关闭语义：当调试状态为 `-1` 或 `1000` 时，服务端发送最后一条日志后关闭连接

#### `key` 的五种模式

| 模式 | 示例 | 实际行为 | 源码依据 |
| --- | --- | --- | --- |
| 搜索调试 | `斗破苍穹` | 按关键字走搜索页 -> 详情页 -> 目录页 -> 正文页 | `Debug.startDebug(bookSource, key)` |
| 详情页调试 | `https://example.com/book/1` | 直接把该 URL 当 `bookUrl` 走详情页调试 | 同上 |
| 发现页调试 | `分类::https://example.com/list` | `::` 后 URL 走发现页调试 | 同上 |
| 目录页调试 | `++https://example.com/toc` | 跳过详情页，直接调目录页 | 同上 |
| 正文页调试 | `--https://example.com/chapter/1` | 直接调正文页 | 同上 |

源码依据：

- `app/src/main/java/io/legado/app/web/socket/BookSourceDebugWebSocket.kt`
- `app/src/main/java/io/legado/app/model/Debug.kt`

---

### 3.2 `ws://127.0.0.1:1123/rssSourceDebug`

- 作用：RSS 源调试
- 首条消息真实可用格式：

```json
{
  "tag": "RSS源URL"
}
```

- 说明：
  - 当前源码只读取 `tag`
  - 不消费 `key`
  - 旧 `api.md` 中的 `key` 描述已过时

- 服务端推送格式：纯文本日志

源码依据：

- `app/src/main/java/io/legado/app/web/socket/RssSourceDebugWebSocket.kt`

---

### 3.3 `ws://127.0.0.1:1123/searchBook`

- 作用：跨书源搜索图书
- 首条消息格式：

```json
{
  "key": "搜索关键词"
}
```

- 服务端推送格式：
  - 每次搜索成功回调时，发送一帧 JSON 字符串
  - 该字符串内容为 `SearchBook[]`
  - 可能多批次发送
  - 搜索结束后关闭连接

源码依据：

- `app/src/main/java/io/legado/app/web/socket/BookSearchWebSocket.kt`

## 4. 数据模型

以下字段均来自 Legado 当前源码定义。若字段未列为“必填”，表示源码允许为空或有默认值。

### 4.1 `BookSource`

源码：`app/src/main/java/io/legado/app/data/entities/BookSource.kt`

| 字段 | 类型 | 必填 | 默认值 | 实际语义 |
| --- | --- | --- | --- | --- |
| `bookSourceUrl` | `string` | 是 | `""` | 书源主键 URL |
| `bookSourceName` | `string` | 是 | `""` | 书源名称 |
| `bookSourceGroup` | `string|null` | 否 | `null` | 分组 |
| `bookSourceType` | `integer` | 否 | `0` | 0文本/1音频/2图片/3文件/4视频 |
| `bookUrlPattern` | `string|null` | 否 | `null` | 详情页 URL 正则 |
| `customOrder` | `integer` | 否 | `0` | 手动排序 |
| `enabled` | `boolean` | 否 | `true` | 是否启用 |
| `enabledExplore` | `boolean` | 否 | `true` | 是否启用发现 |
| `jsLib` | `string|null` | 否 | `null` | JS 库 |
| `enabledCookieJar` | `boolean|null` | 否 | `true` | 是否启用 CookieJar |
| `concurrentRate` | `string|null` | 否 | `null` | 并发率 |
| `header` | `string|null` | 否 | `null` | 请求头规则 |
| `loginUrl` | `string|null` | 否 | `null` | 登录地址或登录 JS |
| `loginUi` | `string|null` | 否 | `null` | 登录表单定义 |
| `loginCheckJs` | `string|null` | 否 | `null` | 登录检测 JS |
| `coverDecodeJs` | `string|null` | 否 | `null` | 封面解密 JS |
| `bookSourceComment` | `string|null` | 否 | `null` | 注释 |
| `variableComment` | `string|null` | 否 | `null` | 自定义变量说明 |
| `lastUpdateTime` | `integer` | 否 | `0` | 最后更新时间 |
| `respondTime` | `integer` | 否 | `180000` | 响应时间 |
| `weight` | `integer` | 否 | `0` | 智能排序权重 |
| `exploreUrl` | `string|null` | 否 | `null` | 发现页 URL |
| `exploreScreen` | `string|null` | 否 | `null` | 发现页筛选规则 |
| `ruleExplore` | `ExploreRule|null` | 否 | `null` | 发现规则 |
| `searchUrl` | `string|null` | 否 | `null` | 搜索 URL |
| `ruleSearch` | `SearchRule|null` | 否 | `null` | 搜索规则 |
| `ruleBookInfo` | `BookInfoRule|null` | 否 | `null` | 详情页规则 |
| `ruleToc` | `TocRule|null` | 否 | `null` | 目录规则 |
| `ruleContent` | `ContentRule|null` | 否 | `null` | 正文规则 |
| `ruleReview` | `ReviewRule|null` | 否 | `null` | 段评规则；当前持久化不稳定 |
| `eventListener` | `boolean` | 否 | `false` | 是否监听事件执行回调 |
| `customButton` | `boolean` | 否 | `false` | 自定义按钮控制 |

### 4.2 书源嵌套规则对象

#### `SearchRule`

源码：`app/src/main/java/io/legado/app/data/entities/rule/SearchRule.kt`

字段：

- `checkKeyWord`
- `bookList`
- `name`
- `author`
- `intro`
- `kind`
- `lastChapter`
- `updateTime`
- `bookUrl`
- `coverUrl`
- `wordCount`

#### `ExploreRule`

源码：`app/src/main/java/io/legado/app/data/entities/rule/ExploreRule.kt`

字段：

- `bookList`
- `name`
- `author`
- `intro`
- `kind`
- `lastChapter`
- `updateTime`
- `bookUrl`
- `coverUrl`
- `wordCount`

#### `BookInfoRule`

源码：`app/src/main/java/io/legado/app/data/entities/rule/BookInfoRule.kt`

字段：

- `init`
- `name`
- `author`
- `intro`
- `kind`
- `lastChapter`
- `updateTime`
- `coverUrl`
- `tocUrl`
- `wordCount`
- `canReName`
- `downloadUrls`

#### `TocRule`

源码：`app/src/main/java/io/legado/app/data/entities/rule/TocRule.kt`

字段：

- `preUpdateJs`
- `chapterList`
- `chapterName`
- `chapterUrl`
- `formatJs`
- `isVolume`
- `isVip`
- `isPay`
- `updateTime`
- `nextTocUrl`

#### `ContentRule`

源码：`app/src/main/java/io/legado/app/data/entities/rule/ContentRule.kt`

字段：

- `content`
- `subContent`
- `title`
- `nextContentUrl`
- `webJs`
- `sourceRegex`
- `replaceRegex`
- `imageStyle`
- `imageDecode`
- `payAction`
- `callBackJs`

### 4.3 `RssSource`

源码：`app/src/main/java/io/legado/app/data/entities/RssSource.kt`

主要字段：

- `sourceUrl`
- `sourceName`
- `sourceIcon`
- `sourceGroup`
- `sourceComment`
- `enabled`
- `variableComment`
- `jsLib`
- `enabledCookieJar`
- `concurrentRate`
- `header`
- `loginUrl`
- `loginUi`
- `loginCheckJs`
- `coverDecodeJs`
- `sortUrl`
- `singleUrl`
- `articleStyle`
- `ruleArticles`
- `ruleNextPage`
- `ruleTitle`
- `rulePubDate`
- `ruleDescription`
- `ruleImage`
- `ruleLink`
- `ruleContent`
- `contentWhitelist`
- `contentBlacklist`
- `shouldOverrideUrlLoading`
- `style`
- `enableJs`
- `loadWithBaseUrl`
- `injectJs`
- `preloadJs`
- `startHtml`
- `startStyle`
- `startJs`
- `showWebLog`
- `lastUpdateTime`
- `customOrder`
- `type`
- `preload`
- `cacheFirst`
- `searchUrl`

### 4.4 `ReplaceRule`

源码：`app/src/main/java/io/legado/app/data/entities/ReplaceRule.kt`

字段：

- `id`
- `name`
- `group`
- `pattern`
- `replacement`
- `scope`
- `scopeTitle`
- `scopeContent`
- `excludeScope`
- `isEnabled`
- `isRegex`
- `timeoutMillisecond`
- `order`

### 4.5 `Book`

源码：`app/src/main/java/io/legado/app/data/entities/Book.kt`

字段：

- `bookUrl`
- `tocUrl`
- `origin`
- `originName`
- `name`
- `author`
- `kind`
- `customTag`
- `coverUrl`
- `customCoverUrl`
- `intro`
- `customIntro`
- `charset`
- `type`
- `group`
- `latestChapterTitle`
- `latestChapterTime`
- `lastCheckTime`
- `lastCheckCount`
- `totalChapterNum`
- `durChapterTitle`
- `durChapterIndex`
- `durVolumeIndex`
- `chapterInVolumeIndex`
- `durChapterPos`
- `durChapterTime`
- `wordCount`
- `canUpdate`
- `order`
- `originOrder`
- `variable`
- `readConfig`
- `syncTime`

`readConfig` 字段：

- `reverseToc`
- `pageAnim`
- `reSegment`
- `imageStyle`
- `useReplaceRule`
- `delTag`
- `ttsEngine`
- `splitLongChapter`
- `readSimulating`
- `startDate`
- `startChapter`
- `dailyChapters`
- `openCredits`
- `closeCredits`
- `playMode`
- `playSpeed`

### 4.6 `BookProgress`

源码：`app/src/main/java/io/legado/app/data/entities/BookProgress.kt`

字段：

- `name`
- `author`
- `durChapterIndex`
- `durChapterPos`
- `durChapterTime`
- `durChapterTitle`

### 4.7 `BookChapter`

源码：`app/src/main/java/io/legado/app/data/entities/BookChapter.kt`

字段：

- `url`
- `title`
- `isVolume`
- `baseUrl`
- `bookUrl`
- `index`
- `isVip`
- `isPay`
- `resourceUrl`
- `tag`
- `wordCount`
- `start`
- `end`
- `startFragmentId`
- `endFragmentId`
- `variable`
- `imgUrl`

### 4.8 `SearchBook`

源码：`app/src/main/java/io/legado/app/data/entities/SearchBook.kt`

字段：

- `bookUrl`
- `origin`
- `originName`
- `type`
- `name`
- `author`
- `kind`
- `coverUrl`
- `intro`
- `wordCount`
- `latestChapterTitle`
- `tocUrl`
- `time`
- `variable`
- `originOrder`
- `chapterWordCountText`
- `chapterWordCount`
- `respondTime`

## 5. 实现注意事项

### 5.1 对 MCP 服务影响最大的兼容点

- `rssSourceDebug` 不接受旧文档里的 `key` 语义，只看 `tag`
- `bookSourceDebug` 的 `tag` 是书源 URL，不是名称
- `bookSourceDebug.key` 有五种模式，MCP 最好做显式参数映射，不要把原始字符串拼接逻辑暴露给上层调用方
- `getReplaceRules` 需要二次 JSON 解析
- `saveReplaceRule` / `deleteReplaceRule` 需要按源码行为做成功推断
- 图片接口必须按二进制处理，不能走 JSON 解析
- HTTP 异常分支可能直接返回文本，MCP 侧不能假设所有响应都是 `ReturnData`

### 5.2 推荐的 MCP 归一化策略

- **对于 HTTP 接口**：统一将 `ReturnData` 转换为包含 `ok`, `normalized_data`, `raw_upstream`, `warnings`, `upstream_endpoint` 的对象，处理 JSON 字符串化数组等边界情况。
- **对于 WebSocket 调试/搜索**：
  - 推荐采用 **单次请求 (One-shot)** 模式：封装启动、等待和结果聚合逻辑。
  - 结果归一化：将原始事件流（Logs 或 SearchBooks）展平，直接返回给调用方，避免复杂的会话生命周期管理。
  - 合理设置超时（推荐 30-60s），确保在多书源搜索或复杂调试场景下能拿到完整结果。

### 5.3 参考源码索引

- HTTP 路由：`app/src/main/java/io/legado/app/web/HttpServer.kt`
- WebSocket 路由：`app/src/main/java/io/legado/app/web/WebSocketServer.kt`
- Web 服务端口：`app/src/main/java/io/legado/app/service/WebService.kt`
- 书源控制器：`app/src/main/java/io/legado/app/api/controller/BookSourceController.kt`
- RSS 控制器：`app/src/main/java/io/legado/app/api/controller/RssSourceController.kt`
- 替换规则控制器：`app/src/main/java/io/legado/app/api/controller/ReplaceRuleController.kt`
- 图书控制器：`app/src/main/java/io/legado/app/api/controller/BookController.kt`
- 调试逻辑：`app/src/main/java/io/legado/app/model/Debug.kt`
