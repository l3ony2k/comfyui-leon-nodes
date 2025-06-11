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

describe

```bash
curl -X POST 'http://localhost:8080/mj/submit/describe' \
  --header 'Content-Type: application/json' \
  --header 'mj-api-secret: sk-midjourney' \
  --header 'X-Api-Key: sk-midjourney' \
  --data-raw '{
  "botType": "MID_JOURNEY",
  "base64": "data:image/jpeg;base64,iVBOR...gg==",
  "accountFilter": {
    "remark": "lzn"
  }
}'
```

the return is like this

```json
{
  "code": 1,
  "description": "Submit success",
  "result": "1748599984985576",
  "properties": {
    "discordChannelId": "1050703772185268251",
    "discordInstanceId": "1648406635623804928"
  }
}
```

poll

```bash
curl -X GET 'http://localhost:8080/mj/task/1748599984985576/fetch' \
  --header 'Content-Type: application/json' \
  --header 'mj-api-secret: sk-midjourney' \
  --header 'X-Api-Key: sk-midjourney' \
  --data-raw ''
```

return

```json
{
  "id": "1748599984985576",
  "properties": {
    "finalZhPrompt": "1️⃣ A simple, flat cartoon drawing of a blonde-haired, blue-eyed woman in a pink dress with puffy sleeves, set against a background of green grass and white clouds in the sky, in the style of Mo Willems and [Craigie Aitchison](https://goo.gl/search?artist%20Craigie%20Aitchison). The image features bright colors and a simple, flat vector clipart of a blond woman wearing large yellow butterfly wings behind her back. \n\n2️⃣ A blonde girl with blue eyes, wearing a pink dress and yellow wings on her back, is standing in a green field. The style is a simple drawing, with simple lines, a blue sky, and a simple background, in the style of a children's book illustration. The colors are flat, with simple shapes and no shading or gradients. The little angel has two hands spread out, making it look like she's flying. \n\n3️⃣ A simple, flat cartoon drawing of a blonde-haired, blue-eyed girl wearing a pink dress. She has large, yellow butterfly wings on her back, and the background features green grass and a sky with clouds. The drawing uses simple shapes and lines, with no shading, resembling a children's coloring book page. \n\n4️⃣ A simple, flat cartoon drawing of a blonde girl with blue eyes wearing a pink dress. She has large, yellow butterfly wings on her back, and the background features green grass and a blue sky. The illustration has a simple, children's book style, with flat colors and shapes.",
    "discordChannelId": "1050703772185268251",
    "botType": "MID_JOURNEY",
    "notifyHook": null,
    "discordInstanceId": "1648406635623804928",
    "flags": 0,
    "messageId": "1377952972033626132",
    "nonce": "1649502263904890880",
    "finalPrompt": "1️⃣ A simple, flat cartoon drawing of a blonde-haired, blue-eyed woman in a pink dress with puffy sleeves, set against a background of green grass and white clouds in the sky, in the style of Mo Willems and [Craigie Aitchison](https://goo.gl/search?artist%20Craigie%20Aitchison). The image features bright colors and a simple, flat vector clipart of a blond woman wearing large yellow butterfly wings behind her back. \n\n2️⃣ A blonde girl with blue eyes, wearing a pink dress and yellow wings on her back, is standing in a green field. The style is a simple drawing, with simple lines, a blue sky, and a simple background, in the style of a children's book illustration. The colors are flat, with simple shapes and no shading or gradients. The little angel has two hands spread out, making it look like she's flying. \n\n3️⃣ A simple, flat cartoon drawing of a blonde-haired, blue-eyed girl wearing a pink dress. She has large, yellow butterfly wings on her back, and the background features green grass and a sky with clouds. The drawing uses simple shapes and lines, with no shading, resembling a children's coloring book page. \n\n4️⃣ A simple, flat cartoon drawing of a blonde girl with blue eyes wearing a pink dress. She has large, yellow butterfly wings on her back, and the background features green grass and a blue sky. The illustration has a simple, children's book style, with flat colors and shapes.",
    "progressMessageId": "1377952972033626132"
  },
  "action": "DESCRIBE",
  "status": "SUCCESS",
  "prompt": "1️⃣ A simple, flat cartoon drawing of a blonde-haired, blue-eyed woman in a pink dress with puffy sleeves, set against a background of green grass and white clouds in the sky, in the style of Mo Willems and [Craigie Aitchison](https://goo.gl/search?artist%20Craigie%20Aitchison). The image features bright colors and a simple, flat vector clipart of a blond woman wearing large yellow butterfly wings behind her back. \n\n2️⃣ A blonde girl with blue eyes, wearing a pink dress and yellow wings on her back, is standing in a green field. The style is a simple drawing, with simple lines, a blue sky, and a simple background, in the style of a children's book illustration. The colors are flat, with simple shapes and no shading or gradients. The little angel has two hands spread out, making it look like she's flying. \n\n3️⃣ A simple, flat cartoon drawing of a blonde-haired, blue-eyed girl wearing a pink dress. She has large, yellow butterfly wings on her back, and the background features green grass and a sky with clouds. The drawing uses simple shapes and lines, with no shading, resembling a children's coloring book page. \n\n4️⃣ A simple, flat cartoon drawing of a blonde girl with blue eyes wearing a pink dress. She has large, yellow butterfly wings on her back, and the background features green grass and a blue sky. The illustration has a simple, children's book style, with flat colors and shapes.",
  "promptEn": "1️⃣ A simple, flat cartoon drawing of a blonde-haired, blue-eyed woman in a pink dress with puffy sleeves, set against a background of green grass and white clouds in the sky, in the style of Mo Willems and [Craigie Aitchison](https://goo.gl/search?artist%20Craigie%20Aitchison). The image features bright colors and a simple, flat vector clipart of a blond woman wearing large yellow butterfly wings behind her back. \n\n2️⃣ A blonde girl with blue eyes, wearing a pink dress and yellow wings on her back, is standing in a green field. The style is a simple drawing, with simple lines, a blue sky, and a simple background, in the style of a children's book illustration. The colors are flat, with simple shapes and no shading or gradients. The little angel has two hands spread out, making it look like she's flying. \n\n3️⃣ A simple, flat cartoon drawing of a blonde-haired, blue-eyed girl wearing a pink dress. She has large, yellow butterfly wings on her back, and the background features green grass and a sky with clouds. The drawing uses simple shapes and lines, with no shading, resembling a children's coloring book page. \n\n4️⃣ A simple, flat cartoon drawing of a blonde girl with blue eyes wearing a pink dress. She has large, yellow butterfly wings on her back, and the background features green grass and a blue sky. The illustration has a simple, children's book style, with flat colors and shapes.",
  "description": "/describe 1748599984985576.jpg",
  "submitTime": 1748599984985,
  "startTime": 1748599988911,
  "finishTime": 1748599995216,
  "progress": "100%",
  "imageUrl": "https://cdn.discordapp.com/ephemeral-attachments/1092492867185950852/1377952966417453166/1748599984985576.jpg?ex=683ad634&is=683984b4&hm=8c3a10f36e6671a10c777fb627afe6ed34cbc008965a6839eed28de2f971462f&",
  "imageHeight": null,
  "imageWidth": null,
  "failReason": null,
  "state": null,
  "buttons": [
    {
      "customId": "MJ::Job::PicReader::1",
      "emoji": "1️⃣",
      "label": "",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::Job::PicReader::2",
      "emoji": "2️⃣",
      "label": "",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::Job::PicReader::3",
      "emoji": "3️⃣",
      "label": "",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::Job::PicReader::4",
      "emoji": "4️⃣",
      "label": "",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::Picread::Retry",
      "emoji": "🔄",
      "label": "",
      "type": 2,
      "style": 2
    },
    {
      "customId": "MJ::Job::PicReader::all",
      "emoji": "🎉",
      "label": "Imagine all",
      "type": 2,
      "style": 2
    }
  ]
}
```

upload a image to discord attachment.

```bash
curl -X POST 'http://localhost:8080/mj/submit/upload-discord-images' \
  --header 'Content-Type: application/json' \
  --header 'mj-api-secret: sk-midjourney' \
  --header 'X-Api-Key: sk-midjourney' \
  --data-raw '{
  "base64Array": ["data:image/jpeg;base64,iVBORw0KGg...g==","data:image/jpeg;base64,iVBORw0KGgoA...ORK5CYII="],
  "filter": {
    "remark": "lzn"
  }
}'
```

for one image only:

```bash
curl -X POST 'http://localhost:8080/mj/submit/upload-discord-images' \
  --header 'Content-Type: application/json' \
  --header 'mj-api-secret: sk-midjourney' \
  --header 'X-Api-Key: sk-midjourney' \
  --data-raw '{
  "base64Array": ["data:image/jpeg;base64,iVBORw0KGgoAAAA...rkJggg=="],
  "filter": {
    "remark": "lzn"
  }
}'
```

the return is like

```json
{
  "code": 1,
  "description": "success",
  "result": [
    "https://cdn.discordapp.com/attachments/1050703772185268251/1377949251270737990/1649498547436974080.jpg?ex=683ad2be&is=6839813e&hm=f44a4a93d233412a545e17eb6ebdfcaf27d93bee59a11fcb40406a4cfe7dd63c&",
    "https://cdn.discordapp.com/attachments/1050703772185268251/1377949251950350346/1649498551039881216.jpg?ex=683ad2be&is=6839813e&hm=65bdcc787f7c3f53527a66c6698b98d912512929b7d9527bbd6f351afc78ea9b&"
  ]
}
```

for only one image:

```json
{
  "code": 1,
  "description": "success",
  "result": [
    "https://cdn.discordapp.com/attachments/1050703772185268251/1379344648903852112/1650893956138987520.jpg?ex=683fe64f&is=683e94cf&hm=bf9ff21541aea62056900a69946de302a96b7dde6d3338d40de73eb5c36ba329&"
  ]
}
```