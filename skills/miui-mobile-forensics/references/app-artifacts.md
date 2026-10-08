# Android App Artifact Reference

This reference captures high-yield artifact locations for MIUI Android phone
forensics. Use it as a checklist, not as a substitute for evidence.

## MIUI Backup Layout

Typical path:

```text
MIUI/MIUI/backup/AllBackup/20250801_104823/<app display>(<package>).bak
```

The directory timestamp is the backup start time in `yyyyMMdd_HHmmss` format.
The `.bak` payload commonly contains a MIUI wrapper followed by:

```text
ANDROID BACKUP
5
0
none
<tar payload>
```

After stripping the text header, the remaining stream is usually an uncompressed
tar of app-private data.

## XBrowser

Package: `com.mmbox.xbrowser.pro`

High-yield file:

```text
apps/com.mmbox.xbrowser.pro/db/mbrowser
```

Tables:
 - `download`: downloaded file path, URL, MIME type, size.
 - `history`: browsing history and titles.
 - `search_his`: search keywords.

## imToken

Package: `im.token.app`

High-yield files:

```text
apps/im.token.app/db/RKStorage
apps/im.token.app/f/walletsV2/*.json
```

Look for:
 - `reduxPersist:db`
 - `WalletModel`
 - `AccountModel`
 - `identifier`
 - `chainType`
 - `address`
 - `imTokenMeta.name`

Count accounts from the account model item list. Address suffix questions should
preserve the original address case when the question asks for exact characters.

## Soul

Package: `cn.soulapp.android`

High-yield files:

```text
apps/cn.soulapp.android/db/soul_app.db
apps/cn.soulapp.android/db/chat_*
apps/cn.soulapp.android/**/groupchat*
```

Look for:
 - current login user ID and nickname in profile/preferences DBs.
 - joined groups in `im_group_bean`.
 - group activity by counting message rows grouped by sender ID for groups where the account is currently joined.
 - `group_nick_name` strings in MMKV files for nickname mapping.

## Tencent Yuanbao and AI Chat Apps

Likely package patterns:
 - `com.tencent.hunyuan.app.chat`
 - app names containing `元宝`, `AI`, `chat`, `assistant`, `hunyuan`

Artifacts to inspect:
 - login/profile SharedPreferences.
 - SQLite chat/history tables.
 - React Native/Flutter storage (`RKStorage`, `AsyncStorage`, local storage).
 - cached request/response JSON.

Fields to search:
 - `nickname`, `nick`, `userName`, `displayName`
 - `prompt`, `question`, `query`, `conversation`, `message`
 - `model`, `modelName`, `llm`, `bot`, `provider`, `agent`

If an answer asks which model was called, require an explicit model/provider
field from the artifact or clearly label the conclusion as tentative.

## Xiaomi Smart Home

Package: `com.xiaomi.smarthome`

Search terms:
 - `roomId`, `room_id`, `homeId`, `did`, `deviceId`
 - camera names and location labels such as `后院`

Room IDs may be stored in cached home JSON, device relationship tables, or
SharedPreferences.

## Clock and Alarm

Packages:
 - `com.android.deskclock`
 - MIUI clock variants under `com.miui.*clock*`

Search terms:
 - `alarm`
 - `hour`, `minutes`, `label`, `enabled`
 - Chinese labels such as `飞机`, `赶飞机`, `航班`

If the app stores minutes since midnight, convert `hour * 60 + minute` back to
`HH:mm`.

## Recording Apps

Common evidence:
 - media/recording SQLite DB.
 - app-private audio metadata JSON.
 - file names containing timestamp strings.

Use app database creation/recording time first. Filesystem modified time is
secondary evidence because extraction can alter it.
