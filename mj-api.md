i think we need a refactor on midjourney images node. the api works like this: there are two parts submit job and fetch job status. when i request this:

```bash
curl -X POST 'http://localhost:8080/mj/submit/imagine' \
  --header 'Content-Type: application/json' \
  --header 'mj-api-secret: sk-midjourney' \
  --header 'X-Api-Key: sk-midjourney' \
  --data-raw '{
    "prompt": "dog playing ball --v 7 --p m7318879261434052637",
    "botType": "MID_JOURNEY",
    "accountFilter": {
      "remark": "lzn"
    }
  }'
```
the return is
```json
{
  "code": 1,
  "description": "Submit success",
  "result": "1748339029401828",
  "properties": {
    "discordChannelId": "1050703772185268251",
    "discordInstanceId": "1648406635623804928"
  }
}
```
so i need to use another request to get status
```bash
curl -X GET 'http://localhost:8080/mj/task/1748339029401828/fetch' \
  --header 'Content-Type: application/json' \
  --header 'mj-api-secret: sk-midjourney' \
  --header 'X-Api-Key: sk-midjourney' \
  --data-raw ''
```
the return is like this 
```json
{
  "id": "1748339029401828",
  "properties": {
    "discordChannelId": "1050703772185268251",
    "botType": "MID_JOURNEY",
    "notifyHook": null,
    "discordInstanceId": "1648406635623804928",
    "flags": 0,
    "messageId": "1376858604266586205",
    "messageHash": "0ddb91a0-af46-4ae9-8e8e-c271074eb6e6",
    "nonce": "1648407736855097344",
    "finalPrompt": "dog playing ball --v 7.0 --p 77724z8",
    "progressMessageId": "1376858432602243142",
    "messageContent": "**dog playing ball --v 7.0 --p 77724z8** - <@1050702627576483930> (relaxed)"
  },
  "action": "IMAGINE",
  "status": "SUCCESS",
  "prompt": "dog playing ball --v 7 --p m7318879261434052637",
  "promptEn": "dog playing ball --v 7 --p m7318879261434052637",
  "description": "/imagine dog playing ball --v 7 --p m7318879261434052637",
  "submitTime": 1748339029401,
  "startTime": 1748339030665,
  "finishTime": 1748339072775,
  "progress": "100%",
  "imageUrl": "https://cdn.discordapp.com/attachments/1050703772185268251/1376858603847417937/lzn9819_dog_playing_ball_0ddb91a0-af46-4ae9-8e8e-c271074eb6e6.png?ex=6836daff&is=6835897f&hm=2afb972387f4fecc7c900fc3f3580f1259458ad019d6f8c535e4faef130248dc&",
  "imageHeight": 2048,
  "imageWidth": 2048,
  "failReason": null,
  "state": null,
  "buttons": [
    {
      "customId": "MJ::JOB::upsample::1::0ddb91a0-af46-4ae9-8e8e-c271074eb6e6",
      "emoji": "",
      "label": "U1",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::JOB::upsample::2::0ddb91a0-af46-4ae9-8e8e-c271074eb6e6",
      "emoji": "",
      "label": "U2",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::JOB::upsample::3::0ddb91a0-af46-4ae9-8e8e-c271074eb6e6",
      "emoji": "",
      "label": "U3",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::JOB::upsample::4::0ddb91a0-af46-4ae9-8e8e-c271074eb6e6",
      "emoji": "",
      "label": "U4",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::JOB::reroll::0::0ddb91a0-af46-4ae9-8e8e-c271074eb6e6::SOLO",
      "emoji": "🔄",
      "label": "",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::JOB::variation::1::0ddb91a0-af46-4ae9-8e8e-c271074eb6e6",
      "emoji": "",
      "label": "V1",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::JOB::variation::2::0ddb91a0-af46-4ae9-8e8e-c271074eb6e6",
      "emoji": "",
      "label": "V2",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::JOB::variation::3::0ddb91a0-af46-4ae9-8e8e-c271074eb6e6",
      "emoji": "",
      "label": "V3",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::JOB::variation::4::0ddb91a0-af46-4ae9-8e8e-c271074eb6e6",
      "emoji": "",
      "label": "V4",
      "type": 2,
      "style": 2
    }
  ]
}
```