#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Author: Hersh Anand
# Email: hanand@salesforce.com
# Copyright: Copyright 2023, Marketing Cloud Peronalization - Slack Bot
# =============================================================================
'''The Module Has Been Built to Integrate MCP with Slack'''
# =============================================================================
# Imports
# =============================================================================
import slack
import os
import re
import yaml
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import requests as reqs
from datetime import datetime
import json
# =============================================================================
# Load Env Variables, YAML Configuration
# =============================================================================
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

with open('config.yaml', 'r') as f:
	cfg = yaml.safe_load(f)

# Set MCP Variables
account = cfg['account']
dataset = cfg['dataset']
uid_campaign = cfg['uid_campaign']
promo_campaign = cfg['promo_campaign']
promo_datafield = cfg['promo_datafield']
uid_datafield = cfg['uid_datafield']
# =============================================================================

# This App will be used for handling event requests from Slack
app = App(token=os.environ['SLACK_BOT_TOKEN'], signing_secret=os.environ['SLACK_SIGNING_SECRET'])

flask_app = Flask(__name__)

default_handler = SlackRequestHandler(app)

@flask_app.route('/slack/events', methods=['POST'])
def events():
	return default_handler.handle(request)

# Create SSC Payload
def create_ssc_payload(user_input):
	ssc = {
		"action": "Get User Information",
		"user": {
			"attributes": {
				"emailAddress": user_input
			}
		},
		"source": {
			"channel": "Server",
			"application": "Slack Bot"
		}
	}
	return ssc

# Create Campaign Stats Payload
def create_campaignStats_payload(campaign_name, experience_id, user_id):
	campaignStats = {
		"action": campaign_name + " Conversion",
		"user": {
			"id": user_id
		},
		"campaignStats": [{
			"experienceId": experience_id,
			"stat": "Click",
			"control": "false"
		}],
		"source": {
			"channel": "server",
			"application": "Slack Bot"
		}
	}
	return campaignStats

# Parse NBA payload
def parse_nba(nba_payload, user_id):
	nba_promos=[]

	# Store experience ID
	experience_id = nba_payload['experienceId']

	# Iterate through NBA payload and create Slack template
	for promo in nba_payload['payload'][promo_datafield]:
		nba_promos_dict= [{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*<"+promo['attributes']['url']['value']+"|"+promo['attributes']['name']['value']+">*\n"+promo['attributes']['description']['value']
			},
			"accessory": {
				"type": "image",
				"image_url": promo['assets'][0]['imageUrl'],
				"alt_text": promo['attributes']['name']['value']
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"action_id": "promo_"+promo['id'],
					"text": {
						"type": "plain_text",
						"text": "Accept"
					},
					"style": "primary",
					"value": promo['attributes']['name']['value']+'_'+experience_id+'_'+user_id
				}
			]
		},
		{
			"type": "divider"
		}
		]

		nba_promos.append(nba_promos_dict)

	return nba_promos


def create_message(name, email, engagement, ts, segments, nba):

	message = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Customer Record for *"+name+":*"
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"fields": [
				{
					"type": "mrkdwn",
					"text": ":email: *Email:* " + email
				},
				{
					"type": "mrkdwn",
					"text": ":date: *Last Activity:* " + ts
				},
				{
					"type": "mrkdwn",
					"text": ":chart_with_upwards_trend: *Engagement Score:* " + engagement
				},
				{
					"type": "mrkdwn",
					"text": ":dart: *Segment Membership:* ```" + segments + "```"
				}
			]
		},
		# Next Best Action
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Next Best Action*"
			}
		},
		{ 
			"type": "divider"
		}
	]

	# Append NBA template to user info template
	for promo_dict in nba:
		for promo in promo_dict:
			message.append(promo)

	return message

@app.action(re.compile('promo_.*'))
def interactions(ack, client, body):
	ack()

	# Parse campaign name, experience ID and user ID
	r_button = body['actions'][0]['value']
	campaign_name, experience_id, user_id = r_button.split('_')

	# Create and call campaign stats payload
	campaignStats_payload = create_campaignStats_payload(campaign_name, experience_id, user_id)
	r_campaignStats = reqs.post('https://'+account+'.evergage.com/api2/authevent/'+dataset, auth=(os.environ['API_KEY'], os.environ['API_SECRET']), json=campaignStats_payload)
	
	# Check if campaign stats call was successful 
	if r_campaignStats.status_code == 200:
		message_text = ':white_check_mark: Sucessfully updated campaign for *' + campaign_name + '*'
	else:
		message_text = ':exclamation: There was an issue. Campaign was not updated.'
		return

	# Send acknowlegement of button response
	response = client.chat_update(
		channel=body['container']['channel_id'],
		ts=body['container']['message_ts'],
		text=message_text
	)
	
	# Post success message in channel
	client.chat_postMessage(channel=body['container']['channel_id'], text=message_text)


@app.command('/einstein')
def einstein(ack, command, client, body):
	ack()
	global user_id, account, dataset, uid_campaign, promo_campaign, promo_datafield, uid_datafield
	
	# Store Slack request
	data = body
	channel_id = data.get('channel_id')
	user_input = data.get('text')

	# Create SSC payload
	ssc_payload = create_ssc_payload(user_input)

	# Call IS to request SS campaigns
	r_ssc = reqs.post('https://'+account+'.evergage.com/api2/authevent/'+dataset, auth=(os.environ['API_KEY'], os.environ['API_SECRET']), json=ssc_payload)
	
	# Store SSC payload
	json_ssc_data = r_ssc.json()

	# Store all raw SSC data
	all_ssc_payload = json_ssc_data['campaignResponses']

	# Search for User ID campaign
	ssc_user_id=next(item for item in all_ssc_payload if item['campaignName'] == uid_campaign)

	# Store User ID
	user_id = ssc_user_id['payload'][uid_datafield]['profileId']['value']['value']

	# Call IS to request user attributes from userID
	r_user = reqs.get('https://'+account+'.evergage.com/api/dataset/'+dataset+'/user/' + user_id, auth=(os.environ['API_KEY'], os.environ['API_SECRET']))
	
	# Check if user exists
	if r_user.status_code == 200:
		# Store User payload
		json_user_data = r_user.json()
	# No user was found
	else:
		client.chat_postMessage(channel=channel_id, text=':exclamation: User *' + user_input + '* could not be found. Please check the ID and try again.')
		return

	# Store user attributes
	segments = "N/A" if json_user_data['segments'] is None else ', '.join(map(str, json_user_data['segments'])) # Convert list to string
	engagement = '{:.1%}'.format(json_user_data['engagementScore']) # Convert float to precentage
	lastActivity = json_user_data['lastActivity']
	name = "N/A" if json_user_data['name'] is None else json_user_data['name']
	email = "N/A" if json_user_data['emailAddress'] is None else json_user_data['emailAddress']
	lastActivity /= 1000 # Convert milliseconds to seconds
	ts = datetime.utcfromtimestamp(lastActivity).strftime('%m/%d/%Y %H:%M:%S') # Format unix timestamp

	# Search NBA campaign
	nba_payload=next(item for item in all_ssc_payload if item['campaignName'] == promo_campaign)

	# Parse NBA campaign
	nba = parse_nba(nba_payload, user_id)

	# Create Slack message
	message = create_message(name, email, engagement, str(ts), segments, nba)

	# Post composed message back to channel
	client.chat_postMessage(channel=channel_id, blocks=message)


if __name__ == '__main__':
	flask_app.run()