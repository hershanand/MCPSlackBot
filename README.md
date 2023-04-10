# Marketing Cloud Personalization - Slack Bot

<p align="center">
	<img src="https://image.s4.sfmc-content.com/lib/fe2b1172766404757c1075/m/1/dcaf653f-5489-405c-83fc-dad88c32bb12.png" alt="MCP Slack Bot" width=50% height=50%>
</p>

## 📖 Summary
This bot was created in order to pull in a user's attributes, segment membership, engagement score and NBA/NBO from Marketing Cloud Personalization into Slack.

## ⚠️ Prerequisites
* Heroku
* Slack
* Marketing Cloud Personalization - Premium Edition
* MCP Promotion Library Setup

## ⚡️ 1. Create Server-Side Template & Campaign, Generate API Keys
1. You’ll need to create 2 server-side templates:
	1. First template should return the list of promotions (reference our [Einstein Decisions template](https://developer.salesforce.com/docs/marketing/personalization/guide/sales-service-cloud-connector-einstein-decisions.html)).
	2. Second template should return the user’s attributes (reference the following [GitHub repo](https://github.com/aaronrileysalesforce/ServerSideTemplates/blob/main/RetrieveAttributes))
2. Next you’ll create a server-side campaign, one for each of the templates. Attach each template to their respected campaign, apply any additional rulesets, and publish.
3. Navigate to **Security → API Tokens** and select the **Generate Token button** to create the API Keys (we will use this later in Heroku)

## 🧬 2. Configure MCP Slack Bot
1. Clone this GitHub repo and open the **config.yaml** file.
    1. Edit **lines 5-10** with your MCP instance information. The **datafield** attributes were set in your server-side template code.
    2. <img src="https://image.s4.sfmc-content.com/lib/fe2b1172766404757c1075/m/1/b855e9cc-5593-43b5-a566-d602cb562fe4.jpg" alt="YAML Config" width=65% height=65%>
2. Create a new app within Heroku and deploy the cloned repo with your modified YAML file.
3. Within the app, navigate to **Settings** and select **Reveal Config Vars button**. Add the following API values you obtained from MCP in Step 1.3 and label them the following:
    1. API_KEY
    2. API_SECRET

## ✨ 3. Create MCP Slack Bot
1. Login to your Slack instance and navigate to [your apps section](https://api.slack.com/apps) and select **Create New App button**.
    1. Select the **From an app manifest** option
    2. Select the workspace the app should be deployed
    3. From the YAML code below, replace the **<HEROKU_VALUE>** (lines 11 and 23) with your Heroku app name from Step 2.2. Then copy and paste the code to your manifest and create the app.

``` yaml
display_information:
  name: MC Personalization
  description: Marketing Cloud Personalization Bot
  background_color: "#d46600"
features:
  bot_user:
    display_name: MC Personalization
    always_online: false
  slash_commands:
    - command: /einstein
      url: https://<HEROKU_VALUE>.herokuapp.com/slack/events
      description: Retrieve user attributes & NBA
      should_escape: false
oauth_config:
  scopes:
    bot:
      - chat:write
      - channels:history
      - commands
settings:
  interactivity:
    is_enabled: true
    request_url: https://<HEROKU_VALUE>.herokuapp.com/slack/events
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```
2. Install the app to your workspace.
3. Once installed, grab the **Signing Secret** (located on the **Basic Information** screen) and the **Bot User OAuth Token** (located on the **OAuth & Permissions** screen)
4. Add these values to your Vars list in Heroku like you did in Step 2.3. Label them the following:
    1. SLACK_BOT_TOKEN
    2. SLACK_SIGNING_SECRET

## 🚀 4. Deploy MCP Slack Bot

1. Within Slack, create a new channel and give it a name.
    1. <img src="https://image.s4.sfmc-content.com/lib/fe2b1172766404757c1075/m/1/c182eaad-29c1-4e6c-9a1a-d03bd0ccfae1.png" alt="Slack - Create Channel" width=40% height=40%>
2. Add the bot by inviting it into the channel using the command **/invite** and selecting **Add apps to this channel**
    1. <img src="https://image.s4.sfmc-content.com/lib/fe2b1172766404757c1075/m/1/bea75df8-b703-4779-8ec5-0ff30d60de2d.png" alt="Slack - Invite Bot" width=35% height=35%>
3. Click **Add** button for the **MC Personalization** app
4. Run the bot by entering the **/einstein** command followed by the user’s e-mail to retrieve back their user attributes and NBO/NBA.  
5. Congrats!! The bot has been successfully deployed and set up within your workspace!! 🥳

## 👨‍💻 Author
Hersh Anand