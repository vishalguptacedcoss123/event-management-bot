import json, requests,os
from flask import Flask, request, make_response, Response
from slackclient import SlackClient
from datetime import timedelta, date
import re,string
import time
from datetime import datetime 
import pymysql
SLACK_TOKEN = 'xoxb-341150331345-nIBRm69thsMHLSWqOWxuhz27'
slack_client = SlackClient(SLACK_TOKEN)
class event_data():
	def __init__(self, appdata):
		self.appdata=appdata
	def routing(self):
		app=self.appdata
		app.add_url_rule("/commit","1_inreative",self.commit_data,methods=["POST","GET"])
		app.add_url_rule("/external_date","external_data_source",self.external_data,methods=["POST","GET"])
		app.add_url_rule("/event","auto_events",self.event_auto,methods=["POST","GET"])
		app.add_url_rule("/menu","user lists",self.check_list,methods=["POST"])
		app.add_url_rule("/manage","user survey",self.manage_survey,methods=["POST"])

	def connection_start(self):
		self.connection = pymysql.connect(
			host='localhost',
			user='root',
			password='',
			db='eventbot',
			charset='utf8mb4',
			cursorclass=pymysql.cursors.DictCursor
		)
		self.cursor = self.connection.cursor()
	def commit_data(self):

		res=request.form.get('payload')
		data= json.loads(res)
		callback_id=data['callback_id']
		print(callback_id)
		print(data)
		if callback_id=="event_has_been_created":
			flag = False
			event = []
			for key,value in data['submission'].items():
				if 'title_' in key:
					flag = True
					event = key
			if flag:
				old_id = event.split("title_",1)[1]
				label=data['submission']['title_'+old_id+'']
				team_id=data['team']['id']
				user_id=data['user']['id']
				user_name=data['user']['name']
				channel_id=data['channel']['id']
				comment=data['submission']['description']
				self.connection_start()
				sql = "INSERT INTO  create_full_event (`event_id`, `team_id`, `user_id`, `user_name`, `label`, `comment`)VALUES(%s ,%s ,%s, %s ,%s, %s)"
				self.cursor.execute(sql, (old_id,team_id,user_id,user_name,label,comment))
				self.connection.commit()
				lastrowid = self.cursor.lastrowid
				lastrowid=str(lastrowid)
				self.cursor.execute("SELECT ts  FROM create_event where event_id='"+old_id+"'")
				result=self.cursor.fetchall()
				message_ts=result[0]['ts']
				message_ts=str(message_ts)
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{
						"text": "your event is *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [     
							{
								"name": "external_date_"+lastrowid,
								"text": "Select a Date",
								"type": "select",
								"data_source": "external",
								"min_query_length": 0,
							},
							{
								"name": "external_time_"+lastrowid,
								"text": "Select Time",
								"type": "select",
								"data_source":"external",
								"min_query_length":0,
							},
							{ 
								"name": "reminder_"+lastrowid,
								"text": "REMINDER",
								"type": "select",                                
								"options": [
									{
										"text": "One's",
										"value": "one_time"
									},
									{
										"text": "Recurring",
										"value": "recurring"
									}
								   
								]
							}
						]
					}       
				]
				fetch=slack_client.api_call('chat.update',ts=message_ts,channel=channel_id,attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_full_event SET ts=%s WHERE id=%s"
				self.cursor.execute(sql, (ts,lastrowid))
				self.connection.commit()
				return Response(""),200	
		elif callback_id=="edit_event":
			flag = False
			edit_info = []
			for key,value in data['submission'].items():
				if 'title_' in key:
					flag = True
					edit_info = key
			if flag:
				id = edit_info.split("title_",1)[1]
				eidt_title=data['submission']['title_'+id+'']
				edit_comment=data['submission']['description']
				self.connection_start()
				self.cursor.execute("SELECT event_id,event_time,event_date,reminder FROM `create_full_event` WHERE id='"+id+"'")
				event=self.cursor.fetchall()
				old_id=str(event[0]['event_id'])
				date=str(event[0]['event_date'])
				time=str(event[0]['event_time'])
				reminder=str(event[0]['reminder'])
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				message_ts=self.cursor.fetchall()
				ts=message_ts[0]['ts']
				self.cursor.execute("update `create_full_event` set label='"+eidt_title+"', comment='"+edit_comment+"' WHERE id='"+id+"'")
				self.connection.commit()
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{
						"text": "Your Event Is *"+eidt_title+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							},
							{
								"title":"Reminder",
								"value": "*"+reminder+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					},
					{
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_event_"+id,
								"text": "Select Event",
								"type": "select",
								"options": [
									{
										"text": "Event Detail",
										"value": "detail"
									},
									{
										"text": "Event Time",
										"value": "time"
									},
									{
										"text": "Event date",
										"value": "date"
									},
									{
										"text": "Event Reminder",
										"value": "reminder"
									},
									{
										"text": "Users",
										"value": "user"
									},
									{
										"text": "Channels",
										"value": "channel"
									}
								   
								]
							}
						]
					}
				]
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()	
				return Response(''),200			

		elif callback_id=="new_event_create":
			action_name=data['actions'][0]['name']
			if 'assign_' in action_name:
				trigger_id=data['trigger_id']
				channel_id=data['channel']['id']
				event_id=action_name.split("assign_",1)[1]
				ts=data['message_ts']
				slack_client.api_call('dialog.open', trigger_id=trigger_id,channel=channel_id,
						dialog={
									"trigger_id":"trigger_id",
									"callback_id": "event_has_been_created",
									"title": "Request a Ride",
									"submit_label": "Request",
									"elements": [
										{
											"type": "text",
											"label": "Title",
											"name": "title_"+event_id,
											
											"placeholder": "your title"
										},
										{
											"type": "textarea",
											"label": "YOUR MESSAGE",
											"name": "description",
											
											"placeholder": "Description"
										}
									 ]
								})
				
				self.connection_start()
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,event_id))
				self.connection.commit()
				return Response(''),200

			elif 'external_date_' in  action_name:
				date=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("external_date_",1)[1]
				self.connection_start()
				sql = "UPDATE create_full_event SET event_date=%s WHERE id=%s"
				self.cursor.execute(sql, (date,id))
				self.connection.commit()
				self.cursor.execute("select event_id,label from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name":"birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [     
							{
								"name": "external_date_"+id,
								"text": "Select a Date",
								"type": "select",
								"data_source": "external",
								"min_query_length": 0,
							},
							{
								"name": "external_time_"+id,
								"text": "Select Time",
								"type": "select",
								"data_source":"external",
								"min_query_length":0,
							},
							{ 
								"name": "reminder_"+id,
								"text": "REMINDER",
								"type": "select",                                
								"options": [
									{
										"text": "One's",
										"value": "one_time"
									},
									{
										"text": "Recurring",
										"value": "recurring"
									}
								   
								]
							}
						]
					},
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							}
						],                           
						"color": "#F35A00"
					}                             
				]
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(""),200
			elif "external_time_" in action_name:
				time=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("external_time_",1)[1]
				self.connection_start()
				sql = "UPDATE create_full_event SET event_time=%s WHERE id=%s"
				self.cursor.execute(sql, (time,id))
				self.connection.commit()
				self.cursor.execute("select event_id,label,event_date from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				date=fetch[0]['event_date']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
				   
					{
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [     
							{
								"name": "external_date_"+id,
								"text": "Select a Date",
								"type": "select",
								"data_source": "external",
								"min_query_length": 0,
							},
							{
								"name": "external_time_"+id,
								"text": "Select Time",
								"type": "select",
								"data_source":"external",
								"min_query_length":0,
							},
							{ 
								"name": "reminder_"+id,
								"text": "REMINDER",
								"type": "select",                                
								"options": [
									{
										"text": "One's",
										"value": "onetime"
									},
									{
										"text": "Recurring",
										"value": "recurring"
									}
								   
								]
							}

						]
					},
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					}
				]
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(""),200
			elif "back_" in action_name:
				id=action_name.split("back_",1)[1]
				self.connection_start()
				self.cursor.execute("select event_id,label,event_date,event_time,reminder from create_full_event where id='"+id+"'")
				fetch=self.cursor.fetchall()				
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				date=fetch[0]['event_date']
				time=fetch[0]['event_time']
				reminder=fetch[0]['reminder']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [     
							{
								"name": "external_date_"+id,
								"text": "Select a Date",
								"type": "select",
								"data_source": "external",
								"min_query_length": 0,
							},
							{
								"name": "external_time_"+id,
								"text": "Select Time",
								"type": "select",
								"data_source":"external",
								"min_query_length":0,
							},
							{ 
								"name": "reminder_"+id,
								"text": "REMINDER",
								"type": "select",                                
								"options": [
									{
										"text": "One's",
										"value": "onetime"
									},
									{
										"text": "Recurring",
										"value": "recurring"
									}
								   
								]
							}

						]
					},
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							},
							{
								"title":"Reminder",
								"value": "*"+reminder+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					}
				]
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200

			elif "reminder_" in action_name:
				reminder=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("reminder_",1)[1]
				self.connection_start()
				sql = "UPDATE create_full_event SET reminder=%s WHERE id=%s"
				self.cursor.execute(sql, (reminder,id))
				self.connection.commit()
				self.cursor.execute("select event_id,label,event_date,event_time from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				date=fetch[0]['event_date']
				time=fetch[0]['event_time']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{   
						"text": "Your Event Is *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [   
							{
								"name": "back_"+id,
								"text": ":leftwards_arrow_with_hook:Back",
								"type": "button",
								"value": "back",
							},   
							{
								"name": "channel_list_"+id,
								"text": "Select Channels",
								"type": "select",
								"data_source": "channels",
								
							},
							{
								"name": "user_list_"+id,
								"text": "Select Users",
								"type": "select",
								"data_source":"users",
							  
							}
						]
					}
				]
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
		  
			elif "channel_list_" in action_name:
				channel_id=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("channel_list_",1)[1]
				self.connection_start()
				self.cursor.execute("select channels_list from create_full_event where id="+id+"")
				fetch1=self.cursor.fetchone()
				if fetch1['channels_list']=='':
					arr=[]
					a={"text":channel_id}
					arr.append(a)
					channel_info=json.dumps(arr)
					sql = "UPDATE create_full_event SET  channels_list=%s WHERE id=%s"
					self.cursor.execute(sql, (channel_info,id))
					self.connection.commit()
				else: 
					arr=(json.loads(fetch1['channels_list']))
					a={"text":channel_id}
					arr.append(a)
					channel_info=json.dumps(arr)
					sql = "UPDATE create_full_event SET  channels_list=%s WHERE id=%s"
					self.cursor.execute(sql, (channel_info,id))
					self.connection.commit()
				self.cursor.execute("select event_id,label from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},                 
					{   
						"text":"Your Event IS *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "back_"+id,
								"text": ":leftwards_arrow_with_hook:Back",
								"type": "button",
								"value": "back",
							},       
							{
								"name": "channel_list_"+id,
								"text": "Select Channels",
								"type": "select",
								"data_source": "channels",
								
							},
							{
								"name": "user_list_"+id,
								"text": "Select Users",
								"type": "select",
								"data_source":"users",
							  
							}
						]
					},
					
				]        
				for res in arr:
					b={ "text":"<#"+res['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "remove_channel_"+id,"text": ":wastebasket:Remove","type": "button","value":res['text']  }   ]   }
					attachments_json12.append(b)
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			
			elif "remove_channel_" in action_name:
				remove_channel_id=data['actions'][0]['value']
				id=action_name.split("remove_channel_",1)[1]
				self.connection_start()
				self.cursor.execute("select channels_list from create_full_event where id="+id+"")
				fetch1=self.cursor.fetchone()
				fetch_c_id=json.loads(fetch1['channels_list'])
				arr=[]
				for  data1 in  fetch_c_id:
					for key,val in data1.items():
						if val==remove_channel_id:
							print("remove")
						else:
							b={key:val}
							arr.append(b)
				last_channel_id=json.dumps(arr)
				sql = "UPDATE create_full_event SET  channels_list=%s WHERE id=%s"
				self.cursor.execute(sql, (last_channel_id,id))
				self.connection.commit()
					

				self.cursor.execute("select event_id,label from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12=[
					{
						 "text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name":"birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},                 
					{   
						"text":"Your Event IS *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "back_"+id,
								"text": ":leftwards_arrow_with_hook:Back",
								"type": "button",
								"value": "back",
							},       
							{
								"name": "channel_list_"+id,
								"text": "Select Channels",
								"type": "select",
								"data_source": "channels",
								
							},
							{
								"name": "user_list_"+id,
								"text": "Select Users",
								"type": "select",
								"data_source":"users",
							  
							}
						]
					}
				]
				for res in arr:
					b={ "text":"<#"+res['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "remove_channel_"+id,"text": ":wastebasket:Remove","type": "button","value":res['text']}]}
					attachments_json12.append(b)
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "user_list_" in action_name:
			
				user_id=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("user_list_",1)[1]
				self.connection_start()
				self.cursor.execute("select user_list from create_full_event where id="+id+"")
				users_fetch=self.cursor.fetchone()
				if users_fetch['user_list']=='':
					user_arr=[]
					a={"text":user_id}
					user_arr.append(a)
					user_info=json.dumps(user_arr)
					sql = "UPDATE create_full_event SET  user_list=%s WHERE id=%s"
					self.cursor.execute(sql, (user_info,id))
					self.connection.commit()
				else: 
					user_arr=(json.loads(users_fetch['user_list']))
					a={"text":user_id}
					user_arr.append(a)
					user_info=json.dumps(user_arr)
					sql = "UPDATE create_full_event SET  user_list=%s WHERE id=%s"
					self.cursor.execute(sql, (user_info,id))
					self.connection.commit()
				self.cursor.execute("select event_id,label from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},                 
					{   
						"text":"Your Event IS *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "back_"+id,
								"text": ":leftwards_arrow_with_hook:Back",
								"type": "button",
								"value": "back",
							},       
							{
								"name": "channel_list_"+id,
								"text": "Select Channels",
								"type": "select",
								"data_source": "channels",
								
							},
							{
								"name": "user_list_"+id,
								"text": "Select Users",
								"type": "select",
								"data_source":"users",
							  
							}
						]
					},
					
				]        
				for user in user_arr:
					b={ "text":"<@"+user['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "remove_user_"+id,"text": ":wastebasket:Remove","type": "button","value":user['text']  }   ]   }
					attachments_json12.append(b)
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			
			elif "remove_user_" in action_name:
				remove_user_id=data['actions'][0]['value']
				id=action_name.split("remove_user_",1)[1]
				self.connection_start()
				self.cursor.execute("select user_list from create_full_event where id="+id+"")
				user=self.cursor.fetchone()
				fetch_u_id=json.loads(user['user_list'])
				user_arr=[]
				for  users in  fetch_u_id:
					for key,val in users.items():
						if val==remove_user_id:
							print("remove")
						else:
							b={key:val}
							user_arr.append(b)
				last_user_id=json.dumps(user_arr)
				sql = "UPDATE create_full_event SET  user_list=%s WHERE id=%s"
				self.cursor.execute(sql, (last_user_id,id))
				self.connection.commit()
				self.cursor.execute("select event_id,label from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12=[
					{
						 "text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name":"birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},                 
					{   
						"text":"Your Event IS *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "back_"+id,
								"text": ":leftwards_arrow_with_hook:Back",
								"type": "button",
								"value": "back",
							},       
							{
								"name": "channel_list_"+id,
								"text": "Select Channels",
								"type": "select",
								"data_source": "channels",
								
							},
							{
								"name": "user_list_"+id,
								"text": "Select Users",
								"type": "select",
								"data_source":"users",
							  
							}
						]
					}
				]
				for user in user_arr:
					b={ "text":"<@"+user['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "remove_channel_"+id,"text": ":wastebasket:Remove","type": "button","value":user['text']}]}
					attachments_json12.append(b)
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			
			elif "select" in action_name:
				id=data['actions'][0]['selected_options'][0]['value']
				self.connection_start()
				self.cursor.execute("select * from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				date=fetch[0]['event_date']
				time=fetch[0]['event_time']
				reminder=fetch[0]['reminder']

				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							},
							{
								"title":"Reminder",
								"value": "*"+reminder+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					},
					{   
						
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_event_"+id,
								"text": "Select Event",
								"type": "select",
								"options": [
									{
										"text": "Event Detail",
										"value": "detail"
									},
									{
										"text": "Event Time",
										"value": "time"
									},
									{
										"text": "Event date",
										"value": "date"
									},
									{
										"text": "Event Reminder",
										"value": "reminder"
									},
									{
										"text": "Users",
										"value": "user"
									},
									{
										"text": "Channels",
										"value": "channel"
									}
								   
								]
							}
						]
					}
				]
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
			elif "edit_time_" in action_name:
				time=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("edit_time_",1)[1]
				self.connection_start()
				sql = "UPDATE create_full_event SET event_time=%s WHERE id=%s"
				self.cursor.execute(sql, (time,id))
				self.connection.commit()
				self.cursor.execute("select * from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				date=fetch[0]['event_date']
				reminder=fetch[0]['reminder']
				sql = "UPDATE create_full_event SET event_date=%s WHERE id=%s"
				self.cursor.execute(sql, (date,id))
				self.connection.commit()
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							},
							{
								"title":"Reminder",
								"value": "*"+reminder+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					},
					{   
						
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_event_"+id,
								"text": "Select Event",
								"type": "select",
								"options": [
									{
										"text": "Event Detail",
										"value": "detail"
									},
									{
										"text": "Event Time",
										"value": "time"
									},
									{
										"text": "Event date",
										"value": "date"
									},
									{
										"text": "Event Reminder",
										"value": "reminder"
									},
									{
										"text": "Users",
										"value": "user"
									},
									{
										"text": "Channels",
										"value": "channel"
									}
								   
								]
							}
						]
					}
				]
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "edit_date_" in action_name:
				date=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("edit_date_",1)[1]
				self.connection_start()
				sql = "UPDATE create_full_event SET event_date=%s WHERE id=%s"
				self.cursor.execute(sql, (date,id))
				self.connection.commit()
				self.cursor.execute("select * from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				time=fetch[0]['event_time']
				reminder=fetch[0]['reminder']
				sql = "UPDATE create_full_event SET event_date=%s WHERE id=%s"
				self.cursor.execute(sql, (date,id))
				self.connection.commit()
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							},
							{
								"title":"Reminder",
								"value": "*"+reminder+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					},
					{   
						
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_event_"+id,
								"text": "Select Event",
								"type": "select",
								"options": [
									{
										"text": "Event Detail",
										"value": "detail"
									},
									{
										"text": "Event Time",
										"value": "time"
									},
									{
										"text": "Event date",
										"value": "date"
									},
									{
										"text": "Event Reminder",
										"value": "reminder"
									},
									{
										"text": "Users",
										"value": "user"
									},
									{
										"text": "Channels",
										"value": "channel"
									}
								   
								]
							}
						]
					}
				]
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200	
			
			elif "edit_alert_" in action_name:
				reminder=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("edit_alert_",1)[1]
				self.connection_start()
				sql = "UPDATE create_full_event SET reminder=%s WHERE id=%s"
				self.cursor.execute(sql, (reminder,id))
				self.connection.commit()
				self.cursor.execute("select * from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				time=fetch[0]['event_time']
				date=fetch[0]['event_date']
				sql = "UPDATE create_full_event SET event_date=%s WHERE id=%s"
				self.cursor.execute(sql, (date,id))
				self.connection.commit()
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							},
							{
								"title":"Reminder",
								"value": "*"+reminder+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					},
					{   
						
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_event_"+id,
								"text": "Select Event",
								"type": "select",
								"options": [
									{
										"text": "Event Detail",
										"value": "detail"
									},
									{
										"text": "Event Time",
										"value": "time"
									},
									{
										"text": "Event date",
										"value": "date"
									},
									{
										"text": "Event Reminder",
										"value": "reminder"
									},
									{
										"text": "Users",
										"value": "user"
									},
									{
										"text": "Channels",
										"value": "channel"
									}
								   
								]
							}
						]
					}
				]
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			
			elif "anniversaryfilter_" in action_name:
				old_id=action_name.split("anniversaryfilter_",1)[1]
				if "anniversary_fullteam"==data['actions'][0]['selected_options'][0]['value']:
					u_list=slack_client.api_call('users.list')
					users_detail=[]
					for details in u_list['members']:
						data_row={
						"text":details['name'],
						"value":details['id']
						}
						users_detail.append(data_row)
					fetch_birthday=[]
					self.connection_start()
					self.cursor.execute("select user_id,birthaday_date from birthady where type='anniversary' ")
					birthday_data=self.cursor.fetchall()
					for element in users_detail:
						for element1 in birthday_data:
							if element['value']==element1['user_id']:
								match_user={
									"user_id":element1['user_id'],
									"anniver_date":element1['birthaday_date']
								}
								fetch_birthday.append(match_user)
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "home_"+old_id,
									"text": ":house:Home",
									"type": "button",
									"value": "home",
								}, 							
								{
									"name": "birthday_"+old_id,
									"text": ":cake:"+"BIRTHDAY",
									"type": "button",
									"value": "birthday",
								}, 			
								{
									"name": "setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "assign_"+old_id,
									"text": "Create Event",
									"type": "button",
									"value": "new_event",
								},
								{
									"name": "select",
									"text": "Show Event",
									"type": "select",
									"options": data_label    
									
								}							
							]
						},
						{	
							"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "anniversaryfilter_"+old_id,
									"text": "Filter",
									"type": "select",
									"options": [
										{
											"text": ":clap:FUll anniversary",
											"value": "anniversary_fullteam"
										},
										{
											"text": ":hugging_face:Your anniversary",
											"value": "anniversary_privatre"
										},
										{
											"text": ":man-bowing:Unknown anniversary",
											"value": "unknown_anniversary"
										}					 
									]
								},
								{
									
									"name": "subteam"+old_id,
									"text": ":busts_in_silhouette:Subteams",
									"type": "button",
									"value": "subteam",
								}
							]						
						}	
					]
					
					for last_f_user in fetch_birthday:
						dates={ "text":"<@"+last_f_user['user_id']+"> \n "+last_f_user['anniver_date']+""}
						attachments_json12.append(dates)
					annivar_data_edit={"fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "editanniversary_"+old_id,"text": ":pencil2:Edit","type": "button","value": "anniversary_tedit",}]}
					attachments_json12.append(annivar_data_edit)
					fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
				elif "anniversary_privatre"==data['actions'][0]['selected_options'][0]['value']:
					self.connection_start()
					self.cursor.execute("select personal_user_name,persoanl_birth_date from personal_birthay where type='anniversary'")
					p_anniversary=self.cursor.fetchall()
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "home_"+old_id,
									"text": ":house:Home",
									"type": "button",
									"value": "home",
								}, 							
								{
									"name": "birthday_"+old_id,
									"text": ":cake:"+"BIRTHDAY",
									"type": "button",
									"value": "birthday",
								}, 			
								{
									"name": "setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "assign_"+old_id,
									"text": "Create Event",
									"type": "button",
									"value": "new_event",
								},
								{
									"name": "select",
									"text": "Show Event",
									"type": "select",
									"options": data_label    
									
								}							
							]
						},
						{	
							"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "anniversaryfilter_"+old_id,
									"text": "Filter",
									"type": "select",
									"options": [
										{
											"text": ":clap:FUll anniversary",
											"value": "anniversary_fullteam"
										},
										{
											"text": ":hugging_face:Your anniversary",
											"value": "anniversary_privatre"
										},
										{
											"text": ":man-bowing:Unknown anniversary",
											"value": "unknown_anniversary"
										}					 
									]
								},
								{
									
									"name":  "anniversary_"+old_id,
									"text": "Done",
									"type": "button",
									"value": "user_detailedit",
								},
								
							]						
						}	
					]
					for private_user in p_anniversary:
						private_dates={ "text":private_user['personal_user_name']+"\n"+ private_user['persoanl_birth_date']}
						attachments_json12.append(private_dates)
					private_edit={"fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "private_anniversaryedit_"+old_id,"text": ":pencil2:Edit","type": "button","value": "anniveredit",}]}
					attachments_json12.append(private_edit)
					fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
				elif "unknown_anniversary"==data['actions'][0]['selected_options'][0]['value']:
					u_list=slack_client.api_call('users.list')
					users_detail=[]
					for details in u_list['members']:
						data_row={
						"text":details['name'],
						"value":details['id']
						}
						users_detail.append(data_row)
					fetch_nouser=[]
					self.connection_start()
					self.cursor.execute("select user_id,birthaday_date from birthady where type='anniversary'")
					birthday_data=self.cursor.fetchall()
					for element in users_detail:
						for element1 in  birthday_data:
							if element1['user_id']!=element['value']:
								match_user={
									"user_id":element['value'],
									"user_name":element['text']
								}
								fetch_nouser.append(match_user)
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "home_"+old_id,
									"text": ":house:Home",
									"type": "button",
									"value": "home",
								}, 							
								{
									"name": "birthday_"+old_id,
									"text": ":cake:"+"BIRTHDAY",
									"type": "button",
									"value": "birthday",
								}, 			
								{
									"name": "setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "assign_"+old_id,
									"text": "Create Event",
									"type": "button",
									"value": "new_event",
								},
								{
									"name": "select",
									"text": "Show Event",
									"type": "select",
									"options": data_label    
									
								}							
							]
						},
						{	
							"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "anniversaryfilter_"+old_id,
									"text": "Filter",
									"type": "select",
									"options": [
										{
											"text": ":clap:FUll anniversary",
											"value": "anniversary_fullteam"
										},
										{
											"text": ":hugging_face:Your anniversary",
											"value": "anniversary_privatre"
										},
										{
											"text": ":man-bowing:Unknown anniversary",
											"value": "unknown_anniversary"
										}					 
									]
								},
								{
									
									"name":  "anniversary_"+old_id,
									"text": "Done",
									"type": "button",
									"value": "user_detailedit",
								},
							]						
						}	
					]
					for unknow_user in fetch_nouser:
						dates={ "text":"<@"+unknow_user['user_id']+">","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "add_anniversary_user_"+unknow_user['user_id'],"text": "Add B-day","type": "button","value": "add_user"},{"name": "ask_anniversary_user_"+unknow_user['user_id'],"text": "Ask Anniv","type": "button","value": "ask_anniversary_user_", "confirm":{"title": "Are you sure?","text": "I'll ask @"+unknow_user['user_name']+" to share anniversary of this user with the team on your behalf?","ok_text": "Yes","dismiss_text": "No"}}] }
						attachments_json12.append(dates)
					fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
			elif "editanniversary_" in action_name:
				old_id=action_name.split("editanniversary_",1)[1]
				u_list=slack_client.api_call('users.list')
				users_detail=[]
				for details in u_list['members']:
					data_row={
					"text":details['name'],
					"value":details['id']
					}
					users_detail.append(data_row)
				fetch_anniversary=[]
				self.connection_start()
				self.cursor.execute("select user_id,birthaday_date from birthady where type='anniversary' ")
				birthday_data=self.cursor.fetchall()
				for element in users_detail:
					for element1 in birthday_data:
						if element['value']==element1['user_id']:
							match_user={
								"user_id":element1['user_id'],
								"b_date":element1['birthaday_date']
							}
							fetch_anniversary.append(match_user)
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 			
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}							   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name":  "anniversary_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							},
							
						]						
					}	
				]
				
				for anniversary_user in fetch_anniversary:
					dates={ "text":"<@"+anniversary_user['user_id']+"> \n "+anniversary_user['b_date']+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"anniversarydate_"+anniversary_user['user_id'],"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}]},{"name":"anniversarymonths_"+anniversary_user['user_id'],"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]}]}				
					attachments_json12.append(dates)
				birth_data_edit={"fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "full_tedit_"+old_id,"text": ":pencil2:Edit","type": "button","value": "full_tedit",}]}
				attachments_json12.append(birth_data_edit)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "private_anniversaryedit_" in action_name:
				old_id=action_name.split("private_anniversaryedit_",1)[1]
				self.connection_start()
				self.cursor.execute("select personal_user_name,persoanl_birth_date from personal_birthay where type='anniversary'")
				p_anniversary=self.cursor.fetchall()
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 			
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*ANNIVERSARY*\n Use the dropdown to filter which anniversary to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "anniversary_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							},
							
						]						
					}	
				]
				for private_user_anniversary in p_anniversary:
					pri_date=private_user_anniversary['persoanl_birth_date']
					main_date=pri_date.split("-")
					dates={ "text":"<@"+private_user_anniversary['personal_user_name']+"> \n "+private_user_anniversary['persoanl_birth_date']+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"private_anniversary_date_"+private_user_anniversary['personal_user_name'],"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":main_date[0],"value":main_date[0]}]},{"name":"private_anniversary_month_"+private_user_anniversary['personal_user_name'],"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":main_date[1],"value":main_date[1]}]}]}				
					attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "private_anniversary_date_" in action_name:
				date=data['actions'][0]['selected_options'][0]['value']
				p_user_name=action_name.split("private_anniversary_date_",1)[1]
				self.connection_start()
				self.cursor.execute("select persoanl_birth_date from personal_birthay where personal_user_name='"+p_user_name+"' and type='anniversary'")
				p_anniversary=self.cursor.fetchall()
				p_user_anniversary=p_anniversary[0]['persoanl_birth_date']
				pre=p_user_anniversary.split("-")
				db_month=pre[1]
				fulldate=""+date+"-"+db_month+""
				sql = "UPDATE personal_birthay SET persoanl_birth_date=%s WHERE personal_user_name=%s and type=%s"
				self.cursor.execute(sql, (fulldate,p_user_name,'anniversary'))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 			
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}							   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name":  "anniversary_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "private_user_detailedit",
							}
						
						]						
					},
				]
				
				
				dates={ "text":"<@"+p_user_name+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"private_anniversary_date_"+p_user_name,"text":date,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":date,"value":date}]},{"name":"private_anniversary_month_"+p_user_name,"text":db_month,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":db_month,"value":db_month}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "private_anniversary_month_" in action_name:
				month=data['actions'][0]['selected_options'][0]['value']
				p_user_name=action_name.split("private_anniversary_month_",1)[1]
				self.connection_start()
				self.cursor.execute("select persoanl_birth_date from personal_birthay where personal_user_name='"+p_user_name+"' and type='anniversary'")
				p_anniversary=self.cursor.fetchall()
				p_user_anniversary=p_anniversary[0]['persoanl_birth_date']
				pre=p_user_anniversary.split("-")
				db_date=pre[0]
				fulldate=""+db_date+"-"+month+""
				sql = "UPDATE personal_birthay SET persoanl_birth_date=%s WHERE personal_user_name=%s and type='anniversary' "
				self.cursor.execute(sql, (fulldate,p_user_name))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 			
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
							}							
						]
					},
					{	
						"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name":  "anniversary_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "private_user_detailedit",
							}
						
						]						
					},
				]
				
				
				dates={ "text":"<@"+p_user_name+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"private_anniversary_date_"+p_user_name,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":db_date,"value":db_date}]},{"name":"private_anniversary_month_"+p_user_name,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":month,"value":month}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200

			elif "anniversarydate_" in action_name:
				date=data['actions'][0]['selected_options'][0]['value']
				user_id=action_name.split("anniversarydate_",1)[1]
				self.connection_start()
				self.cursor.execute("select user_id,birthaday_date from birthady where user_id='"+user_id+"' and type='anniversary'")
				ub_date=self.cursor.fetchall()
				user_birthday=ub_date[0]['birthaday_date']
				p=user_birthday.split("-")
				db_month=p[1]
				fulldate=""+date+"-"+db_month+""
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type='anniversary'"
				self.cursor.execute(sql, (fulldate,user_id))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 			
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*anniversary*\n Use the dropdown to filter which anniversary_ to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name":  "anniversary_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							}
						
						]						
					},
				]				
				dates={ "text":"<@"+ub_date[0]['user_id']+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"anniversarydate_"+ub_date[0]['user_id'],"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":date,"value":date}]},{"name":"anniversarymonths_"+ub_date[0]['user_id'],"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":db_month,"value":db_month}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			
			elif "anniversarymonths_" in action_name:
				month=data['actions'][0]['selected_options'][0]['value']
				user_id=action_name.split("anniversarymonths_",1)[1]
				self.connection_start()
				self.cursor.execute("select user_id,birthaday_date from birthady where user_id='"+user_id+"' and type='anniversary'")
				ub_date=self.cursor.fetchall()
				user_birthday=ub_date[0]['birthaday_date']
				p=user_birthday.split("-")
				db_date=p[0]
				fulldate=""+db_date+"-"+month+""
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type='anniversary'"
				self.cursor.execute(sql, (fulldate,user_id))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 			
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name":  "anniversary_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							}
						
						]						
					},
				]				
				dates={ "text":"<@"+ub_date[0]['user_id']+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"anniversarydate_"+ub_date[0]['user_id'],"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":db_date,"value":db_date}]},{"name":"anniversarymonths_"+ub_date[0]['user_id'],"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":month,"value":month}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			
			elif "add_anniversary_user_" in action_name:
				user_id=action_name.split("add_anniversary_user_",1)[1]
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				team_id=data['team']['id']
				assign_by=data['user']['id']
				self.connection_start()
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 			
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}						   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name":  "anniversary_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							},
							
						]						
					}	
				]
			
				dates={ "text":"<@"+user_id+">","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"unkowndateuser_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}]},{"name":"userkonwmonth_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]}]}
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				birth="anniversary"
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				sql = "INSERT INTO  birthady (`user_id`, `team_id` , `added_by`, `type`)VALUES(%s, %s, %s,%s)"
				self.cursor.execute(sql, (user_id,team_id,assign_by,birth))
				self.connection.commit()
				return Response(''),200
			elif "ask_anniversary_user_" in action_name:
				user_id=action_name.split("ask_anniversary_user_",1)[1]
				assign_by=data['user']['id']
				team_id=data['team']['id']
				birth="anniversary"
				self.connection_start()
				sql = "INSERT INTO  birthady (`user_id`, `team_id` , `added_by`,`type`)VALUES(%s, %s, %s,%s)"
				self.cursor.execute(sql, (user_id,team_id,assign_by, birth))
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 			
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "anniversary_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							}
						]						
					}	
				]				
				dates={ "text":"<@"+user_id+">","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "add_anniversary_user_"+user_id,"text": "Add anniversary","type": "button","value": "add_user"}] }
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				attachments_json = [
					{
						"text": "Hey, I'm EvevtManageBot! \nI keep everyone informed about upcoming birthdays and post anniversary greetings. :anniversary:Welcome to *general136* subteam on #general.\nYou will receive reminders and congratulations for upcoming anniversary of subteam members.\nIt looks like I don't know your anniversary - wanna share with the team? ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "self_anniversary_"+user_id,
								"text": "Add anniversary",
								"type": "button",
								"value": "add_anniversary",
							}							
						]
					}
				]		
				slack_client.api_call('chat.postMessage',ts=data['message_ts'],channel=user_id,attachments=attachments_json,as_user=True)
				return Response(''),200
			elif "self_anniversary_" in action_name:
				user_id=action_name.split("self_anniversary_",1)[1]
				attachments_json12=[{ "text":"<@"+user_id+">","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"seluserdate_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}]},{"name":"userselfmonth_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]},{"name": "anniversarycancel_"+user_id,"text": ":negative_squared_cross_mark:Cancel","type": "button","value": "cancel"}]}]
				slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,link_names=True,as_user=True)	
				return Response(''),200
				
			elif "seluserdate_" in action_name:
				print("lknsdlnslsndvlj")
				anniversary_date=data['actions'][0]['selected_options'][0]['value']
				user_id=action_name.split("seluserdate_",1)[1]
				jan="jan"
				fulldate=""+anniversary_date+"-"+jan+""
				self.connection_start()
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type=%s"
				self.cursor.execute(sql, (fulldate,user_id,'anniversary'))
				self.connection.commit()
				attachments_json12=[{ "text":"<@"+user_id+"> \n "+anniversary_date+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"seluserdate_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":anniversary_date,"value":anniversary_date}]},{"name":"userselfmonth_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]},{"name": "anniversarycancel_"+user_id,"text": ":negative_squared_cross_mark:Cancel","type": "button","value": "cancel"}]}]
				slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,link_names=True,as_user=True)	
				return Response(''),200

			elif "userselfmonth_" in action_name:
				anniversary_month=data['actions'][0]['selected_options'][0]['value']
				user_id=action_name.split("userselfmonth_",1)[1]
				self.connection_start()
				self.cursor.execute("select birthaday_date from birthady where user_id='"+user_id+"' and type='anniversary'")
				p_anniversary=self.cursor.fetchall()
				p_user_anniversary=p_anniversary[0]['birthaday_date']
				pre=p_user_anniversary.split("-")
				db_date=pre[0]
				fulldate=""+db_date+"-"+anniversary_month+""		
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type=%s"
				self.cursor.execute(sql, (fulldate,user_id,'anniversary'))
				self.connection.commit()
				attachments_json12=[{ "text":"<@"+user_id+">\n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"seluserdate_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}]},{"name":"userselfmonth_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]},{"name": "anniversarydone_"+user_id,"text": "Done","type": "button","value": "done"}]}]
				slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,link_names=True,as_user=True)	
				return Response(''),200
			
			elif "anniversarycancel_" in action_name :
				user_id=action_name.split("anniversarycancel_",1)[1]
				self.connection_start()
				self.cursor.execute("DELETE FROM `birthady` WHERE   user_id='"+user_id+"' and type='anniversary'")
				self.connection.commit()
				attachments_json12=[{ "text":"<@"+user_id+">","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"seluserdate_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}]},{"name":"userselfmonth_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]},{"name": "anniversarycancel_"+user_id,"text": ":negative_squared_cross_mark:Cancel","type": "button","value": "cancel"}]}]
				slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,link_names=True,as_user=True)	
				return Response(''),200
			elif "anniversarydone_" in action_name:
				user_id=action_name.split("anniversarydone_",1)[1]
				self.connection_start()
				self.cursor.execute("select birthaday_date from birthady where user_id='"+user_id+"' and type='anniversary'")
				anniversary_date=self.cursor.fetchall()
				attachments_json12=[{ "text":"<@"+user_id+"> \n "+anniversary_date[0]['birthaday_date']+"\n THank for set your anniversary Date."}]
				slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,link_names=True,as_user=True)	
				return Response(''),200

			elif "unkowndateuser_" in action_name:
				anniversary_user_id=action_name.split("unkowndateuser_",1)[1]
				assign_by=data['user']['id']
				team_id=data['team']['id']
				jan="jan"
				date=data['actions'][0]['selected_options'][0]['value']
				fulldate=""+date+"-"+jan+""
				self.connection_start()
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type=%s"
				self.cursor.execute(sql, (fulldate,anniversary_user_id,'anniversary'))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 		
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}							   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "privatedetaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "private_user_detailedit",
							}
						
						]						
					},
				]	
				dates={ "text":"<@"+anniversary_user_id+"> \n "+date+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"unkowndateuser_"+anniversary_user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":date,"value":date}]},{"name":"userkonwmonth_"+anniversary_user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "userkonwmonth_" in action_name:
				unknown_user_anniversary_id=action_name.split("userkonwmonth_",1)[1]
				month=data['actions'][0]['selected_options'][0]['value']
				self.connection_start()
				self.cursor.execute("select birthaday_date from birthady where user_id='"+unknown_user_anniversary_id+"' and type='anniversary'")
				unkown_anniversary_date=self.cursor.fetchall()
				install_date=unkown_anniversary_date[0]['birthaday_date']
				old_date=install_date.split("-")
				unknow_user_date=old_date[0]
				fulldate=""+unknow_user_date+"-"+month+""
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type=%s"
				self.cursor.execute(sql, (fulldate,unknown_user_anniversary_id,'anniversary'))
				self.connection.commit()				
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 		
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "privatedetaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "private_user_detailedit",
							}
						
						]						
					},
				]
				
	
				dates={ "text":"<@"+unknown_user_anniversary_id+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"unkowndateuser_"+unknown_user_anniversary_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":unknow_user_date,"value":unknow_user_date}]},{"name":"userkonwmonth_"+unknown_user_anniversary_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":month,"value":month}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
								
			elif "edit_user_" in action_name:
				user_id=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("edit_user_",1)[1]
				self.connection_start()
				self.cursor.execute("select user_list from create_full_event where id="+id+"")
				users_fetch=self.cursor.fetchone()
				if users_fetch['user_list']=='':
					user_arr=[]
					a={"text":user_id}
					user_arr.append(a)
					user_info=json.dumps(user_arr)
					sql = "UPDATE create_full_event SET  user_list=%s WHERE id=%s"
					self.cursor.execute(sql, (user_info,id))
					self.connection.commit()
				else: 
					user_arr=(json.loads(users_fetch['user_list']))
					a={"text":user_id}
					user_arr.append(a)
					user_info=json.dumps(user_arr)
					sql = "UPDATE create_full_event SET  user_list=%s WHERE id=%s"
					self.cursor.execute(sql, (user_info,id))
					self.connection.commit()
				self.cursor.execute("select event_id,label,event_time,event_date,reminder from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				date=fetch[0]['event_date']
				time=fetch[0]['event_time']
				reminder=fetch[0]['reminder']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					}, 
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							},
							{
								"title":"Reminder",
								"value": "*"+reminder+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					},                
					{   
						"text":"Your Event IS *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_user_"+id,
								"text": "Select Users",
								"type": "select",
								"data_source":"users",
							},
							{
									"name": "edit_done_"+id,
									"text": "DONE",
									"type": "button",
									"value": "edit_done",
							}
						]
					}
					
				]        
				for user in user_arr:
					b={ "text":"<@"+user['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "edit_r_user_"+id,"text": ":wastebasket:Remove","type": "button","value":user['text']  }   ]   }
					attachments_json12.append(b)
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif 'edit_r_user_' in action_name:
				remove_user_id=data['actions'][0]['value']
				id=action_name.split("edit_r_user_",1)[1]
				self.connection_start()
				self.cursor.execute("select user_list from create_full_event where id="+id+"")
				user=self.cursor.fetchone()
				fetch_u_id=json.loads(user['user_list'])
				user_arr=[]
				for  users in  fetch_u_id:
					for key,val in users.items():
						if val==remove_user_id:
							print("remove")
						else:
							b={key:val}
							user_arr.append(b)
				last_user_id=json.dumps(user_arr)
				sql = "UPDATE create_full_event SET  user_list=%s WHERE id=%s"
				self.cursor.execute(sql, (last_user_id,id))
				self.connection.commit()
				self.cursor.execute("select event_id,label from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12=[
					{
						 "text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},                 
					{   
						"text":"Your Event IS *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_user_"+id,
								"text": "Select Users",
								"type": "select",
								"data_source":"users",
							},
							{
									"name": "edit_done_"+id,
									"text": "DONE",
									"type": "button",
									"value": "edit_done",
							}
						]
					}
				]
				for user in user_arr:
					b={ "text":"<@"+user['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "edit_r_user_"+id,"text": ":wastebasket:Remove","type": "button","value":user['text']}]}
					attachments_json12.append(b)
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "edit_channel_" in action_name:
				channel_id=data['actions'][0]['selected_options'][0]['value']
				id=action_name.split("edit_channel_",1)[1]
				self.connection_start()
				self.cursor.execute("select channels_list from create_full_event where id="+id+"")
				channel_fetch=self.cursor.fetchone()
				if channel_fetch['channels_list']=='':
					channel_arr=[]
					a={"text":channel_id}
					channel_arr.append(a)
					user_info=json.dumps(channel_arr)
					sql = "UPDATE create_full_event SET  channels_list=%s WHERE id=%s"
					self.cursor.execute(sql, (user_info,id))
					self.connection.commit()
				else: 
					channel_arr=(json.loads(channel_fetch['channels_list']))
					a={"text":channel_id}
					channel_arr.append(a)
					channel_info=json.dumps(channel_arr)
					sql = "UPDATE create_full_event SET  channels_list=%s WHERE id=%s"
					self.cursor.execute(sql, (channel_info,id))
					self.connection.commit()
				self.cursor.execute("select event_id,label,event_time,event_date,reminder from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				date=fetch[0]['event_date']
				time=fetch[0]['event_time']
				reminder=fetch[0]['reminder']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					}, 
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							},
							{
								"title":"Reminder",
								"value": "*"+reminder+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					},                
					{   
						"text":"Your Event IS *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_user_"+id,
								"text": "Select Users",
								"type": "select",
								"data_source":"users",
							},
							{
									"name": "edit_done_"+id,
									"text": "DONE",
									"type": "button",
									"value": "edit_done",
							}
						]
					}
					
				]        
				for channel in channel_arr:
					b={ "text":"<#"+channel['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "edit_r_channel_"+id,"text": ":wastebasket:Remove","type": "button","value":channel['text']  }   ]   }
					attachments_json12.append(b)
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif 'edit_r_channel_' in action_name:
				remove_channel_id=data['actions'][0]['value']
				id=action_name.split("edit_r_channel_",1)[1]
				self.connection_start()
				self.cursor.execute("select channels_list from create_full_event where id="+id+"")
				user=self.cursor.fetchone()
				fetch_c_id=json.loads(user['channels_list'])
				channel_arr=[]
				for  users in  fetch_c_id:
					for key,val in users.items():
						if val==remove_channel_id:
							print("remove")
						else:
							b={key:val}
							channel_arr.append(b)
				last_channel_id=json.dumps(channel_arr)
				sql = "UPDATE create_full_event SET  channels_list=%s WHERE id=%s"
				self.cursor.execute(sql, (last_channel_id,id))
				self.connection.commit()
				self.cursor.execute("select event_id,label from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
				ts1=self.cursor.fetchall()
				ts=str(ts1[0]['ts'])
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12=[
					{
						 "text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},                 
					{   
						"text":"Your Event IS *"+label+"*",
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_user_"+id,
								"text": "Select Users",
								"type": "select",
								"data_source":"users",
							},
							{
									"name": "edit_done_"+id,
									"text": "DONE",
									"type": "button",
									"value": "edit_done",
							}
						]
					}
				]
				for channel in channel_arr:
					b={ "text":"<#"+channel['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "edit_r_channel_"+id,"text": ":wastebasket:Remove","type": "button","value":channel['text']}]}
					attachments_json12.append(b)
				fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200

			elif "edit_done_" in action_name:
				id=action_name.split("edit_done_",1)[1]
				self.connection_start()
				self.cursor.execute("select * from create_full_event where id="+id+"")
				fetch=self.cursor.fetchall()
				old_id=fetch[0]['event_id']
				label=fetch[0]['label']
				date=fetch[0]['event_date']
				time=fetch[0]['event_time']
				reminder=fetch[0]['reminder']
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name":"birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "event_setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "our_select_"+old_id,
								"text": "Select Event",
								"type": "select",
								"options":data_label,
							},
							{
								"name": "assign_"+old_id,
								"text": ":memo:New Event",
								"type": "button",
								"value": "new_event",
							} 
						]
					},
					{
						"text": "Your Event Is *"+label+"*",
						"fields": [
							{
								"title": "Date",
								"value": "*"+date+"*",
								"short": True
							},
							{
								"title": " Time",
								"value": "*"+time+"*",
								"short": True
							},
							{
								"title":"Reminder",
								"value": "*"+reminder+"*",
								"short": True
							}
						],
						"color": "#F35A00"
					},
					{   
						
						"fallback":"THIS ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [ 
							{
								"name": "edit_event_"+id,
								"text": "Select Event",
								"type": "select",
								"options": [
									{
										"text": "Event Detail",
										"value": "detail"
									},
									{
										"text": "Event Time",
										"value": "time"
									},
									{
										"text": "Event date",
										"value": "date"
									},
									{
										"text": "Event Reminder",
										"value": "reminder"
									},
									{
										"text": "Users",
										"value": "user"
									},
									{
										"text": "Channels",
										"value": "channel"
									}
								   
								]
							}
						]
					}
				]
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "birthday_" in  action_name:
				old_id=action_name.split("birthday_",1)[1]
				user_id=data['user']['id']
				self.connection_start()
				self.cursor.execute("select user_id from birthady where type='birthday'")
				birthday_data=self.cursor.fetchall()						
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							}
						]						
					}	
				]
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			
			elif "selfuser_" in action_name:
				user_id=action_name.split("selfuser_",1)[1]
				print(data)
				attachments_json12=[{ "text":"<@"+user_id+">","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"userselfdate_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}]},{"name":"selfusermonth_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]},{"name": "cancel"+user_id,"text": ":negative_squared_cross_mark:Cancel","type": "button","value": "cancel"}]}]
				slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,link_names=True,as_user=True)	
				return Response(''),200
				
			elif 'userselfdate_' in action_name:
				self_date=data['actions'][0]['selected_options'][0]['value']
				user_id=action_name.split("userselfdate_",1)[1]
				jan="jan"
				fulldate=""+self_date+"-"+jan+""
				self.connection_start()
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type=%s"
				self.cursor.execute(sql, (fulldate,user_id,'birthday'))
				self.connection.commit()
				attachments_json12=[{ "text":"<@"+user_id+"> \n "+self_date+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"userselfdate_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":self_date,"value":self_date}]},{"name":"selfusermonth_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]},{"name": "cancel"+user_id,"text": ":negative_squared_cross_mark:Cancel","type": "button","value": "cancel"}]}]
				slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,link_names=True,as_user=True)	
				return Response(''),200

			elif "selfusermonth_" in action_name:
				self_month=data['actions'][0]['selected_options'][0]['value']
				user_id=action_name.split("selfusermonth_",1)[1]
				self.connection_start()
				self.cursor.execute("select birthaday_date from birthady where user_id='"+user_id+"' and type='birthday'")
				p_birthday=self.cursor.fetchall()
				p_user_birthday=p_birthday[0]['birthaday_date']
				pre=p_user_birthday.split("-")
				db_date=pre[0]
				fulldate=""+db_date+"-"+self_month+""		
				self.connection_start()
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type=%s"
				self.cursor.execute(sql, (fulldate,user_id,'birthday'))
				self.connection.commit()
				attachments_json12=[{ "text":"<@"+user_id+"> \n "+fulldate+"\n THank for set your Birthday date."}]
				slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,link_names=True,as_user=True)	
				return Response(''),200

			elif "filter_" in action_name:
				old_id=action_name.split("filter_",1)[1]
				if "fullteam"==data['actions'][0]['selected_options'][0]['value']:
					u_list=slack_client.api_call('users.list')
					users_detail=[]
					for details in u_list['members']:
						data_row={
						"text":details['name'],
						"value":details['id']
						}
						users_detail.append(data_row)
					fetch_birthday=[]
					self.connection_start()
					self.cursor.execute("select user_id,birthaday_date from birthady where type='birthday' ")
					birthday_data=self.cursor.fetchall()
					for element in users_detail:
						for element1 in birthday_data:
							if element['value']==element1['user_id']:
								match_user={
									"user_id":element1['user_id'],
									"b_date":element1['birthaday_date']
								}
								fetch_birthday.append(match_user)
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "home_"+old_id,
									"text": ":house:Home",
									"type": "button",
									"value": "home",
								}, 							
								{
									"name": "anniversary_"+old_id,
									"text": ":tada:"+"anniversary",
									"type": "button",
									"value": "edit",
								},
								{
									"name": "setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "assign_"+old_id,
									"text": "Create Event",
									"type": "button",
									"value": "new_event",
								},
								{
									"name": "select",
									"text": "Show Event",
									"type": "select",
									"options": data_label    
									
								}							
							]
						},
						{	
							"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "filter_"+old_id,
									"text": "Filter",
									"type": "select",
									"options": [
										{
											"text": ":clap:FUll Team",
											"value": "fullteam"
										},
										{
											"text": ":hugging_face:Your Bithdays",
											"value": "privatre"
										},
										{
											"text": ":man-bowing:Unknown Birthdays ",
											"value": "unknown_birthdat"
										}								   
									]
								},
								{
									
									"name": "subteam"+old_id,
									"text": ":busts_in_silhouette:Subteams",
									"type": "button",
									"value": "subteam",
								}
							]						
						}	
					]
					self.cursor.execute("select * from bot_birthday ")
					bot=self.cursor.fetchall()
					for last_f_user in fetch_birthday:
						dates={ "text":"<@"+last_f_user['user_id']+"> \n "+last_f_user['b_date']+""}
						attachments_json12.append(dates)
					bot_data={ "text":"<@"+bot[0]['bot_id']+"> \n "+bot[0]['bot_date']+""}
					attachments_json12.append(bot_data)
					birth_data_edit={"fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "full_tedit_"+old_id,"text": ":pencil2:Edit","type": "button","value": "full_tedit",}]}
					attachments_json12.append(birth_data_edit)
					fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
				elif "privatre"==data['actions'][0]['selected_options'][0]['value']:
					self.connection_start()
					self.cursor.execute("select personal_user_name,persoanl_birth_date from personal_birthay where type='birthday'")
					p_birthday=self.cursor.fetchall()
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "home_"+old_id,
									"text": ":house:Home",
									"type": "button",
									"value": "home",
								}, 							
								{
									"name": "anniversary_"+old_id,
									"text": ":tada:"+"anniversary",
									"type": "button",
									"value": "edit",
								},
								{
									"name": "setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "assign_"+old_id,
									"text": "Create Event",
									"type": "button",
									"value": "new_event",
								},
								{
									"name": "select",
									"text": "Show Event",
									"type": "select",
									"options": data_label    
									
								}							
							]
						},
						{	
							"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "filter_"+old_id,
									"text": "Filter",
									"type": "select",
									"options": [
										{
											"text": ":clap:FUll Team",
											"value": "fullteam"
										},
										{
											"text": ":hugging_face:Your Bithdays",
											"value": "privatre"
										},
										{
											"text": ":man-bowing:Unknown Birthdays ",
											"value": "unknown_birthdat"
										}								   
									]
								},
								{
									
									"name": "subteam"+old_id,
									"text": ":busts_in_silhouette:Subteams",
									"type": "button",
									"value": "subteam",
								}
							]						
						}	
					]
					
					for private_user in p_birthday:
						private_dates={ "text":"<@"+private_user['personal_user_name']+"> \n "+private_user['persoanl_birth_date']+""}
						attachments_json12.append(private_dates)
					
					private_edit={"fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "privateedit_"+old_id,"text": ":pencil2:Edit","type": "button","value": "privateedit",}]}
					attachments_json12.append(private_edit)
					fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200

				elif "unknown_birthdat"==data['actions'][0]['selected_options'][0]['value']:
					u_list=slack_client.api_call('users.list')
					users_detail=[]
					for details in u_list['members']:
						data_row={
						"text":details['name'],
						"value":details['id']
						}
						users_detail.append(data_row)
					fetch_nouser=[]
					self.connection_start()
					self.cursor.execute("select user_id,birthaday_date from birthady where type='birthday'")
					birthday_data=self.cursor.fetchall()
					# users_detail_set=set(users_detail)
					# # print(users_detail_set)
					# # print(type(users_detail))
					for element in users_detail:
						print(element)
						flag = False
						for element1 in  birthday_data:
							print(element1)
							if element1['user_id']!=element['value']:
								flag = True
						if flag:
							match_user={
								"user_id":element['value'],
								"user_name":element['text']
							}
							fetch_nouser.append(match_user)
					print(fetch_nouser)
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
						data_row = {
							"text": custom_label['label'],
							"value": custom_label['id']
						}
						data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "home_"+old_id,
									"text": ":house:Home",
									"type": "button",
									"value": "home",
								}, 							
								{
									"name": "anniversary_"+old_id,
									"text": ":tada:"+"anniversary",
									"type": "button",
									"value": "edit",
								},
								{
									"name": "setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "assign_"+old_id,
									"text": "Create Event",
									"type": "button",
									"value": "new_event",
								},
								{
									"name": "select",
									"text": "Show Event",
									"type": "select",
									"options": data_label    
									
								}							
							]
						},
						{	
							"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "filter_"+old_id,
									"text": "Filter",
									"type": "select",
									"options": [
										{
											"text": ":clap:FUll Team",
											"value": "fullteam"
										},
										{
											"text": ":hugging_face:Your Bithdays",
											"value": "privatre"
										},
										{
											"text": ":man-bowing:Unknown Birthdays ",
											"value": "unknown_birthdat"
										}								   
									]
								},
								{
									
									"name": "subteam"+old_id,
									"text": ":busts_in_silhouette:Subteams",
									"type": "button",
									"value": "subteam",
								}
							]						
						}	
					]
					for unknow_user in fetch_nouser:
						dates={ "text":"<@"+unknow_user['user_id']+">","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "adduser_"+unknow_user['user_id'],"text": "Add B-day","type": "button","value": "add_user"},{"name": "askuser_"+unknow_user['user_id'],"text": "Ask B-day","type": "button","value": "ask_user", "confirm":{"title": "Are you sure?","text": "I'll ask @"+unknow_user['user_name']+" to share birthday of this user with the team on your behalf?","ok_text": "Yes","dismiss_text": "No"}}] }
						attachments_json12.append(dates)
					fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
			elif "adduser_" in action_name:
				user_id=action_name.split("adduser_",1)[1]
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				team_id=data['team']['id']
				assign_by=data['user']['id']
				self.connection_start()
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "detaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							},
							
						]						
					}	
				]
			
				dates={ "text":"<@"+user_id+">","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"unkown_date_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}]},{"name":"unkown_month_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]}]}
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				birth="birthday"
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				sql = "INSERT INTO  birthady (`user_id`, `team_id` , `added_by`, `type`)VALUES(%s, %s, %s,%s)"
				self.cursor.execute(sql, (user_id,team_id,assign_by,birth))
				self.connection.commit()
				return Response(''),200
			elif "askuser_" in action_name:
				user_id=action_name.split("askuser_",1)[1]
				assign_by=data['user']['id']
				team_id=data['team']['id']
				birth="birthday"
				self.connection_start()
				sql = "INSERT INTO  birthady (`user_id`, `team_id` , `added_by`,`type`)VALUES(%s, %s, %s,%s)"
				self.cursor.execute(sql, (user_id,team_id,assign_by,birth))
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "detaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							}
						]						
					}	
				]				
				dates={ "text":"<@"+user_id+">","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "adduser_"+user_id,"text": "Add B-day","type": "button","value": "add_user"}] }
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				attachments_json = [
					{
						"text": "Hey, I'm EvevtManageBot! \nI keep everyone informed about upcoming birthdays and post birthdays greetings. :birthday:Welcome to *general136* subteam on #general.\nYou will receive reminders and congratulations for upcoming birthdays of subteam members.\nIt looks like I don't know your birthday - wanna share with the team? ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "selfuser_"+user_id,
								"text": "Add B-Day",
								"type": "button",
								"value": "add_bathady",
							}							
						]
					}
				]		
				slack_client.api_call('chat.postMessage',ts=data['message_ts'],channel=user_id,attachments=attachments_json,as_user=True)
				return Response(''),200

			elif "unkown_date_" in action_name:
				unknown_user_id=action_name.split("unkown_date_",1)[1]
				assign_by=data['user']['id']
				team_id=data['team']['id']
				jan="jan"
				date=data['actions'][0]['selected_options'][0]['value']
				fulldate=""+date+"-"+jan+""
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type=%s"
				self.cursor.execute(sql, (fulldate,unknown_user_id,'birthday'))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "privatedetaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "private_user_detailedit",
							}
						
						]						
					},
				]
				
	
				dates={ "text":"<@"+unknown_user_id+"> \n "+date+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"unkown_date_"+unknown_user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":date,"value":date}]},{"name":"unkown_month_"+unknown_user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "unkown_month_" in action_name:
				unknown_user_id=action_name.split("unkown_month_",1)[1]
				month=data['actions'][0]['selected_options'][0]['value']
				self.connection_start()
				self.cursor.execute("select birthaday_date from birthady where user_id='"+unknown_user_id+"' and type='birthday'")
				unkown_date=self.cursor.fetchall()
				install_date=unkown_date[0]['birthaday_date']
				old_date=install_date.split("-")
				unknow_user_date=old_date[0]
				fulldate=""+unknow_user_date+"-"+month+""
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type=%s"
				self.cursor.execute(sql, (fulldate,unknown_user_id,'birthday'))
				self.connection.commit()				
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "privatedetaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "private_user_detailedit",
							}
						
						]						
					},
				]
				
	
				dates={ "text":"<@"+unknown_user_id+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"unkown_date_"+unknown_user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":unknow_user_date,"value":unknow_user_date}]},{"name":"unkown_month_"+unknown_user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":month,"value":month}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200


			elif "privateedit_" in action_name:
				old_id=action_name.split("privateedit_",1)[1]
				self.connection_start()
				self.cursor.execute("select personal_user_name,persoanl_birth_date from personal_birthay where type='birthday'")
				p_birthday=self.cursor.fetchall()
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "detaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							},
							
						]						
					}	
				]
				for private_user in p_birthday:
					pri_date=private_user['persoanl_birth_date']
					main_date=pri_date.split("-")
					dates={ "text":"<@"+private_user['personal_user_name']+"> \n "+private_user['persoanl_birth_date']+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"privatedate_"+private_user['personal_user_name'],"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":main_date[0],"value":main_date[0]}]},{"name":"privatemonth_"+private_user['personal_user_name'],"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":main_date[1],"value":main_date[1]}]}]}				
					attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "privatedate_" in action_name:
				date=data['actions'][0]['selected_options'][0]['value']
				p_user_name=action_name.split("privatedate_",1)[1]
				self.connection_start()
				self.cursor.execute("select persoanl_birth_date from personal_birthay where personal_user_name='"+p_user_name+"' and type='birthday'")
				p_birthday=self.cursor.fetchall()
				p_user_birthday=p_birthday[0]['persoanl_birth_date']
				pre=p_user_birthday.split("-")
				db_month=pre[1]
				fulldate=""+date+"-"+db_month+""
				sql = "UPDATE personal_birthay SET persoanl_birth_date=%s WHERE personal_user_name=%s and type=%s"
				self.cursor.execute(sql, (fulldate,p_user_name,'birthday'))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "privatedetaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "private_user_detailedit",
							}
						
						]						
					},
				]
				
				
				dates={ "text":"<@"+p_user_name+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"privatedate_"+p_user_name,"text":date,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":date,"value":date}]},{"name":"privatemonth_"+p_user_name,"text":db_month,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":db_month,"value":db_month}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "privatemonth_" in action_name:
				month=data['actions'][0]['selected_options'][0]['value']
				p_user_name=action_name.split("privatemonth_",1)[1]
				self.connection_start()
				self.cursor.execute("select persoanl_birth_date from personal_birthay where personal_user_name='"+p_user_name+"' and type='birthday'")
				p_birthday=self.cursor.fetchall()
				p_user_birthday=p_birthday[0]['persoanl_birth_date']
				pre=p_user_birthday.split("-")
				db_date=pre[0]
				fulldate=""+db_date+"-"+month+""
				sql = "UPDATE personal_birthay SET persoanl_birth_date=%s WHERE personal_user_name=%s and type='birthday' "
				self.cursor.execute(sql, (fulldate,p_user_name))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "privatedetaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "private_user_detailedit",
							}
						
						]						
					},
				]
				
				
				dates={ "text":"<@"+p_user_name+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"privatedate_"+p_user_name,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":db_date,"value":db_date}]},{"name":"privatemonth_"+p_user_name,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":month,"value":month}]}]}				
				attachments_json12.append(dates)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200

			elif "full_tedit_" in action_name:
				old_id=action_name.split("full_tedit_",1)[1]
				u_list=slack_client.api_call('users.list')
				users_detail=[]
				for details in u_list['members']:
					data_row={
					"text":details['name'],
					"value":details['id']
					}
					users_detail.append(data_row)
				fetch_birthday=[]
				self.connection_start()
				self.cursor.execute("select user_id,birthaday_date from birthady where type='birthday' ")
				birthday_data=self.cursor.fetchall()
				for element in users_detail:
					for element1 in birthday_data:
						if element['value']==element1['user_id']:
							match_user={
								"user_id":element1['user_id'],
								"b_date":element1['birthaday_date']
							}
							fetch_birthday.append(match_user)
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "detaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							},
							
						]						
					}	
				]
				self.cursor.execute("select * from bot_birthday ")
				bot=self.cursor.fetchall()
				for last_f_user in fetch_birthday:
					dates={ "text":"<@"+last_f_user['user_id']+"> \n "+last_f_user['b_date']+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"fullteamdate_"+last_f_user['user_id'],"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}]},{"name":"fullteammonths_"+last_f_user['user_id'],"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}]}]}				
					attachments_json12.append(dates)
				bot_data={ "text":"<@"+bot[0]['bot_id']+"> \n "+bot[0]['bot_date']+""}
				attachments_json12.append(bot_data)
				birth_data_edit={"fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "full_tedit_"+old_id,"text": ":pencil2:Edit","type": "button","value": "full_tedit",}]}
				attachments_json12.append(birth_data_edit)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "fullteamdate_" in action_name:
				date=data['actions'][0]['selected_options'][0]['value']
				user_id=action_name.split("fullteamdate_",1)[1]
				self.connection_start()
				self.cursor.execute("select birthaday_date from birthady where user_id='"+user_id+"' and type='birthday'")
				ub_date=self.cursor.fetchall()
				user_birthday=ub_date[0]['birthaday_date']
				p=user_birthday.split("-")
				db_month=p[1]
				fulldate=""+date+"-"+db_month+""
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type='birthday'"
				self.cursor.execute(sql, (fulldate,user_id))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "detaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							}
						
						]						
					},
				]
				self.cursor.execute("select * from bot_birthday ")
				bot=self.cursor.fetchall()
				dates={ "text":"<@"+user_id+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"fullteamdate_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":date,"value":date}]},{"name":"fullteammonths_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":db_month,"value":db_month}]}]}				
				attachments_json12.append(dates)
				bot_data={ "text":"<@"+bot[0]['bot_id']+"> \n "+bot[0]['bot_date']+""}
				attachments_json12.append(bot_data)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200

			elif "fullteammonths_" in action_name:
				month=data['actions'][0]['selected_options'][0]['value']
				user_id=action_name.split("fullteammonths_",1)[1]
				self.connection_start()
				self.cursor.execute("select birthaday_date from birthady where user_id='"+user_id+"' and type='birthday'")
				ub_date=self.cursor.fetchall()
				user_birthday=ub_date[0]['birthaday_date']
				p=user_birthday.split("-")
				db_date=p[0]
				fulldate=""+db_date+"-"+month+""
				sql = "UPDATE birthady SET birthaday_date=%s WHERE user_id=%s and type=%s"
				self.cursor.execute(sql, (fulldate,user_id,'birthday'))
				self.connection.commit()
				event_id=data['original_message']['attachments'][0]['actions'][0]['name']
				old_id=event_id.split("home_",1)[1]
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							},
							{
								
								"name": "detaildone_"+old_id,
								"text": "Done",
								"type": "button",
								"value": "user_detailedit",
							}
						
						]						
					}
				]
				self.cursor.execute("select * from bot_birthday ")
				bot=self.cursor.fetchall()
				dates={ "text":"<@"+user_id+"> \n "+fulldate+"","fallback":"THIS folt by slack ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"fullteamdate_"+user_id,"type":"select","options": [{"text": "01","value": "01"},{"text": "02","value": "02"},{"text": "03","value": "03"},{"text": "04","value": "04"},{"text": "05","value": "05"},{"text": "06","value": "06"},{"text": "07","value": "07"},{"text": "08","value": "08"},{"text": "09","value": "09"},{"text": "10","value": "10"},{"text": "11","value": "11"},{"text": "12","value": "12"},{"text": "13","value": "13"},{"text": "14","value": "14"},{"text": "15","value": "15"},{"text": "16","value": "16"},{"text": "17","value": "17"},{"text": "18","value": "18"},{"text": "19","value": "19"},{"text": "20","value": "10"},{"text": "21","value": "21"},{"text": "22","value": "22"},{"text": "23","value": "23"},{"text": "24","value": "24"},{"text": "25","value": "25"},{"text": "26","value": "26"},{"text": "27","value": "27"},{"text": "28","value": "28"},{"text": "29","value": "29"},{"text": "30","value": "30"},{"text": "31","value": "31"}],"selected_options":[{"text":db_date,"value":db_date}]},{"name":"fullteammonths_"+user_id,"type":"select","options": [{"text": "Jan","value": "jan"},{"text": "Feb","value": "feb"},{"text": "March","value": "march"},{"text": "Apr","value": "apr"},{"text": "May","value": "may"},{"text": "Jun","value": "jun"},{"text": "Jul","value": "Jul"},{"text": "Aug","value": "aug"},{"text": "Sep","value": "sep"},{"text": "Oct","value": "oct"},{"text": "Nov","value": "Nov"},{"text": "Dec","value": "dec"}],"selected_options":[{"text":month,"value":month}]}]}				
				attachments_json12.append(dates)
				bot_data={ "text":"<@"+bot[0]['bot_id']+"> \n "+bot[0]['bot_date']+""}
				attachments_json12.append(bot_data)
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
			elif "detaildone_" in action_name:
				old_id=action_name.split("detaildone_",1)[1]
				user_id=data['user']['id']
				self.connection_start()
				self.cursor.execute("select user_id from birthady where type='birthday' ")
				birthday_data=self.cursor.fetchall()						
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					},
					{	
						"text":"*BIRTHDAYS*\n Use the dropdown to filter which birthdays to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "filter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll Team",
										"value": "fullteam"
									},
									{
										"text": ":hugging_face:Your Bithdays",
										"value": "privatre"
									},
									{
										"text": ":man-bowing:Unknown Birthdays ",
										"value": "unknown_birthdat"
									}								   
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							}
						]						
					}	
				]
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200
				
			elif "home_" in action_name:
				old_id=action_name.split("home_",1)[1]
				self.connection_start()
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 							
							{
								"name": "anniversary_"+old_id,
								"text": ":tada:"+"anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}							
						]
					}
				]
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200

			elif  "edit_event_" in action_name:
				if "detail" == data['actions'][0]['selected_options'][0]['value']:
					id=action_name.split("edit_event_",1)[1]
					self.connection_start()
					self.cursor.execute("select event_id,label,comment from create_full_event where id="+id+"")
					fetch=self.cursor.fetchall()
					old_id=fetch[0]['event_id']
					label=fetch[0]['label']	
					comment=fetch[0]['comment']
					ts=data['message_ts']
					slack_client.api_call('dialog.open', trigger_id=data['trigger_id'],channel=data['channel']['id'],
							dialog={
										"trigger_id":"trigger_id",
										"callback_id": "edit_event",
										"title": "Request a Ride",
										"submit_label": "Request",
										"elements": [
											{
												"type": "text",
												"label": "Title",
												"name": "title_"+id,
												"value":label,
												"placeholder": "your title"
											},
											{
												"type": "textarea",
												"label": "YOUR MESSAGE",
												"name": "description",
												"value":comment,
												"placeholder": "Description"
											}
										 ]
									})
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
				elif "time" == data['actions'][0]['selected_options'][0]['value']:
						id=action_name.split("edit_event_",1)[1]
						self.connection_start()
						self.cursor.execute("select event_id,label,event_time,event_date,reminder from create_full_event where id="+id+"")
						fetch=self.cursor.fetchall()
						old_id=fetch[0]['event_id']
						label=fetch[0]['label']	
						time=fetch[0]['event_time']	
						date=fetch[0]['event_date']	
						reminder=fetch[0]['reminder']	
						self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
						ts=self.cursor.fetchall()
						self.cursor.execute("select * from create_full_event")
						result1=self.cursor.fetchall()
						data_label=[]
						for custom_label in result1:
								data_row = {
									"text": custom_label['label'],
									"value": custom_label['id']
								}
								data_label.append(data_row)
						attachments_json12 = [
							{
								"text": " *Features*\n Select Your Event ",
								"fallback":"THIS folt by slack ",
								"callback_id": "new_event_create",
								"color": "#3AA3E3",
								"attachment_type": "default",
								"actions": [
									{
										"name": "birthday_"+old_id,
										"text": ":cake:"+"BIRTHDAY",
										"type": "button",
										"value": "birthday",
									}, 							
									{
										"name": "anniversary",
										"text": ":tada:"+"anniversary",
										"type": "button",
										"value": "edit",
									},
									{
										"name": "event_setting_"+old_id,
										"text": ":gear:Setting",
										"type": "button",
										"value": "setting",
									},
									{
										"name": "our_select_"+old_id,
										"text": "Select Event",
										"type": "select",
										"options":data_label,
									},
									{
										"name": "assign_"+old_id,
										"text": ":memo:New Event",
										"type": "button",
										"value": "new_event",
									} 
								]
							},
							{
								"text": "Your Event Is *"+label+"*",
								"fields": [
									{
										"title": "Date",
										"value": "*"+date+"*",
										"short": True
									},
									{
										"title": " Time",
										"value": "*"+time+"*",
										"short": True
									},
									{
										"title":"Reminder",
										"value": "*"+reminder+"*",
										"short": True
									}
								],
								"color": "#F35A00"
							},
							{
								"fallback":"THIS ",
								"callback_id": "new_event_create",
								"color": "#3AA3E3",
								"attachment_type": "default",
								"actions": [     
									{
										"name": "edit_time_"+id,
										"text": "Select a Time",
										"type": "select",
										"data_source": "external",
										"min_query_length": 0,
									}
								]
							}
						]
						fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
						ts=fetch['ts']
						sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
						self.cursor.execute(sql, (ts,old_id))
						self.connection.commit()
						return Response(''),200
				elif "reminder" == data['actions'][0]['selected_options'][0]['value']:
					id=action_name.split("edit_event_",1)[1]
					self.connection_start()
					self.cursor.execute("select event_id,label,event_time,event_date,reminder from create_full_event where id="+id+"")
					fetch=self.cursor.fetchall()
					old_id=fetch[0]['event_id']
					label=fetch[0]['label']	
					time=fetch[0]['event_time']	
					date=fetch[0]['event_date']	
					reminder=fetch[0]['reminder']	
					self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
					ts=self.cursor.fetchall()
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
							data_row = {
								"text": custom_label['label'],
								"value": custom_label['id']
							}
							data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name":"birthday_"+old_id,
									"text": ":cake:"+"BIRTHDAY",
									"type": "button",
									"value": "birthday",
								}, 							
								{
									"name": "anniversary",
									"text": ":tada:"+"anniversary",
									"type": "button",
									"value": "edit",
								},
								{
									"name": "event_setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "our_select_"+old_id,
									"text": "Select Event",
									"type": "select",
									"options":data_label,
								},
								{
									"name": "assign_"+old_id,
									"text": ":memo:New Event",
									"type": "button",
									"value": "new_event",
								} 
							]
						},
						{
							"text": "Your Event Is *"+label+"*",
							"fields": [
								{
									"title": "Date",
									"value": "*"+date+"*",
									"short": True
								},
								{
									"title": " Time",
									"value": "*"+time+"*",
									"short": True
								},
								{
									"title":"Reminder",
									"value": "*"+reminder+"*",
									"short": True
								}
							],
							"color": "#F35A00"
						},
						{
							"fallback":"THIS ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [     
								{ 
									"name": "edit_alert_"+id,
									"text": "REMINDER",
									"type": "select",                                
									"options": [
										{
											"text": "One's",
											"value": "onetime"
										},
										{
											"text": "Recurring",
											"value": "recurring"
										}
									]
								}
							]
						}
					]
								   
					fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
				elif "date" == data['actions'][0]['selected_options'][0]['value']:
					id=action_name.split("edit_event_",1)[1]
					self.connection_start()
					self.cursor.execute("select event_id,label,event_time,event_date,reminder from create_full_event where id="+id+"")
					fetch=self.cursor.fetchall()
					old_id=fetch[0]['event_id']
					label=fetch[0]['label']	
					time=fetch[0]['event_time']	
					date=fetch[0]['event_date']	
					reminder=fetch[0]['reminder']	
					self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
					ts=self.cursor.fetchall()
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
							data_row = {
								"text": custom_label['label'],
								"value": custom_label['id']
							}
							data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "birthday_"+old_id,
									"text": ":cake:"+"BIRTHDAY",
									"type": "button",
									"value": "birthday",
								}, 							
								{
									"name": "anniversary",
									"text": ":tada:"+"anniversary",
									"type": "button",
									"value": "edit",
								},
								{
									"name": "event_setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "our_select_"+old_id,
									"text": "Select Event",
									"type": "select",
									"options":data_label,
								},
								{
									"name": "assign_"+old_id,
									"text": ":memo:New Event",
									"type": "button",
									"value": "new_event",
								} 
							]
						},
						{
							"text": "Your Event Is *"+label+"*",
							"fields": [
								{
									"title": "Date",
									"value": "*"+date+"*",
									"short": True
								},
								{
									"title": " Time",
									"value": "*"+time+"*",
									"short": True
								},
								{
									"title":"Reminder",
									"value": "*"+reminder+"*",
									"short": True
								}
							],
							"color": "#F35A00"
						},
						{
							"fallback":"THIS ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [     
								{
									"name": "edit_date_"+id,
									"text": "Select a Date",
									"type": "select",
									"data_source": "external",
									"min_query_length": 0,
								}							
							]	
						}
					]
					fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
				elif "user" == data['actions'][0]['selected_options'][0]['value']:
					id=action_name.split("edit_event_",1)[1]
					self.connection_start()
					self.cursor.execute("select event_id,label,event_time,event_date,reminder from create_full_event where id="+id+"")
					fetch=self.cursor.fetchall()
					old_id=fetch[0]['event_id']
					label=fetch[0]['label']	
					time=fetch[0]['event_time']	
					date=fetch[0]['event_date']	
					reminder=fetch[0]['reminder']
					self.cursor.execute("select user_list from create_full_event where id="+id+"")
					user=self.cursor.fetchone()
					user_arr=[]
					print(user)
					if user['user_list']:
						fetch_u_id=json.loads(user['user_list'])
						user_arr=[]
						for  users in  fetch_u_id:
							for key,val in users.items():
								m={key:val}
								user_arr.append(m)
					self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
					ts=self.cursor.fetchall()
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
							data_row = {
								"text": custom_label['label'],
								"value": custom_label['id']
							}
							data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "birthday_"+old_id,
									"text": ":cake:"+"BIRTHDAY",
									"type": "button",
									"value": "birthday",
								}, 							
								{
									"name": "anniversary",
									"text": ":tada:"+"anniversary",
									"type": "button",
									"value": "edit",
								},
								{
									"name": "event_setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "our_select_"+old_id,
									"text": "Select Event",
									"type": "select",
									"options":data_label,
								},
								{
									"name": "assign_"+old_id,
									"text": ":memo:New Event",
									"type": "button",
									"value": "new_event",
								} 
							]
						},
						{
							"text": "Your Event Is *"+label+"*",
							"fields": [
								{
									"title": "Date",
									"value": "*"+date+"*",
									"short": True
								},
								{
									"title": " Time",
									"value": "*"+time+"*",
									"short": True
								},
								{
									"title":"Reminder",
									"value": "*"+reminder+"*",
									"short": True
								}
							],
							"color": "#F35A00"
						},
						{
							"fallback":"THIS ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [     
								{
									"name": "edit_user_"+id,
									"text": "Select Users",
									"type": "select",
									"data_source": "users",
									
								}
							]
						}
					]
					for user in user_arr:
						b={ "text":"<@"+user['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "edit_r_user_"+id,"text": ":wastebasket:Remove","type": "button","value":user['text']}]}
						attachments_json12.append(b)
					fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
				elif "channel" == data['actions'][0]['selected_options'][0]['value']:
					id=action_name.split("edit_event_",1)[1]
					self.connection_start()
					self.cursor.execute("select event_id,label,event_time,event_date,reminder from create_full_event where id="+id+"")
					fetch=self.cursor.fetchall()
					old_id=fetch[0]['event_id']
					label=fetch[0]['label']	
					time=fetch[0]['event_time']	
					date=fetch[0]['event_date']	
					reminder=fetch[0]['reminder']
					self.cursor.execute("select channels_list from create_full_event where id="+id+"")
					user=self.cursor.fetchone()
					channel_arr=[]
					if user['channels_list']:
						fetch_c_id=json.loads(user['channels_list'])
						channel_arr=[]
						for  users in  fetch_c_id:
							for key,val in users.items():
								m={key:val}
								channel_arr.append(m)
					self.cursor.execute("SELECT ts FROM `create_event` WHERE event_id='"+old_id+"'")
					ts=self.cursor.fetchall()
					self.cursor.execute("select * from create_full_event")
					result1=self.cursor.fetchall()
					data_label=[]
					for custom_label in result1:
							data_row = {
								"text": custom_label['label'],
								"value": custom_label['id']
							}
							data_label.append(data_row)
					attachments_json12 = [
						{
							"text": " *Features*\n Select Your Event ",
							"fallback":"THIS folt by slack ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "birthday_"+old_id,
									"text": ":cake:"+"BIRTHDAY",
									"type": "button",
									"value": "birthday",
								}, 							
								{
									"name": "anniversary",
									"text": ":tada:"+"anniversary",
									"type": "button",
									"value": "edit",
								},
								{
									"name": "event_setting_"+old_id,
									"text": ":gear:Setting",
									"type": "button",
									"value": "setting",
								},
								{
									"name": "our_select_"+old_id,
									"text": "Select Event",
									"type": "select",
									"options":data_label,
								},
								{
									"name": "assign_"+old_id,
									"text": ":memo:New Event",
									"type": "button",
									"value": "new_event",
								} 
							]
						},
						{
							"text": "Your Event Is *"+label+"*",
							"fields": [
								{
									"title": "Date",
									"value": "*"+date+"*",
									"short": True
								},
								{
									"title": " Time",
									"value": "*"+time+"*",
									"short": True
								},
								{
									"title":"Reminder",
									"value": "*"+reminder+"*",
									"short": True
								}
							],
							"color": "#F35A00"
						},
						{
							"fallback":"THIS ",
							"callback_id": "new_event_create",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [     
								{
									"name": "edit_channel_"+id,
									"text": "Select Users",
									"type": "select",
									"data_source": "channels",
									
								}
							]
						}
					]
					for channel in channel_arr:
						b={ "text":"<#"+channel['text']+">","fallback":"THIS ","callback_id": "new_event_create","color": "#3AA3E3","attachment_type": "default","actions":[{"name": "edit_r_channel_"+id,"text": ":wastebasket:Remove","type": "button","value":channel['text']}]}
						attachments_json12.append(b)
					fetch=slack_client.api_call('chat.update',ts=ts,channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
					ts=fetch['ts']
					sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
					self.cursor.execute(sql, (ts,old_id))
					self.connection.commit()
					return Response(''),200
			elif "anniversary_" in action_name:
				old_id=action_name.split("anniversary_",1)[1]
				user_id=data['user']['id']
				self.connection_start()
				# self.cursor.execute("select user_id from birthady where type='anniversary'")
				# birthday_data=self.cursor.fetchall()						
				self.cursor.execute("select * from create_full_event")
				result1=self.cursor.fetchall()
				data_label=[]
				for custom_label in result1:
					data_row = {
						"text": custom_label['label'],
						"value": custom_label['id']
					}
					data_label.append(data_row)
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "home_"+old_id,
								"text": ":house:Home",
								"type": "button",
								"value": "home",
							}, 							
							{
								"name": "birthday_"+old_id,
								"text": ":cake:"+"BIRTHDAY",
								"type": "button",
								"value": "birthday",
							},
							{
								"name": "setting_"+old_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "assign_"+old_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
							}							
						]
					},
					{	
						"text":"*anniversary*\n Use the dropdown to filter which anniversary to show:",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "anniversaryfilter_"+old_id,
								"text": "Filter",
								"type": "select",
								"options": [
									{
										"text": ":clap:FUll anniversary",
										"value": "anniversary_fullteam"
									},
									{
										"text": ":hugging_face:Your anniversary",
										"value": "anniversary_privatre"
									},
									{
										"text": ":man-bowing:Unknown anniversary",
										"value": "unknown_anniversary"
									}					 
								]
							},
							{
								
								"name": "subteam"+old_id,
								"text": ":busts_in_silhouette:Subteams",
								"type": "button",
								"value": "subteam",
							}
						]						
					}	
				]
				fetch=slack_client.api_call('chat.update',ts=data['message_ts'],channel=data['channel']['id'],attachments=attachments_json12,as_user=True)
				ts=fetch['ts']
				sql = "UPDATE create_event SET ts=%s WHERE event_id=%s"
				self.cursor.execute(sql, (ts,old_id))
				self.connection.commit()
				return Response(''),200	
		elif callback_id=="polling_votes":
			print(data)

			action_name=data['actions'][0]['name']
			poll_id=action_name.split('option_',1)[1]
			value=data['actions'][0]['value']
			self.connection_start()
			self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
			resul=self.cursor.fetchone()
			old_option=resul['poll_option']
			qus=resul['poll_tittel']
			fetch_optin=json.loads(old_option)
			onevote_oneuser=resul['max_vote_user']
			print(onevote_oneuser)
			full_option=[]
			i=1
			for option_data in fetch_optin:
				o={"option"+str(i):option_data['option']}
				full_option.append(o)
				i=i+1	
			length=len(full_option)
			option1=full_option[0]['option1']
			option2=full_option[1]['option2']
			if length > 2:
				option3=full_option[2]['option3']
			else:
				option3=None
			if length > 3:
				option4=full_option[3]['option4']
			else:
				option4=None
			if length > 4:
				option5=full_option[4]['option5']
			else:
				option5=None
			if length > 5:
				option6=full_option[5]['option6']
			else:
				option6=None
			if length > 6:
				option7=full_option[6]['option7']
			else:
				option7=None
			if length > 7:
				option8=full_option[7]['option8']
			else:
				option8=None


			attachments_json12=[
				{
					"text": " *"+qus+"* ",
					"fallback":"THIS slack ",
					"callback_id": "polling_votes",
					"color": "#3AA3E3",
					"attachment_type": "default",
					"actions": [
						{
							"name": "option_"+poll_id,
							"text":option1,
							"type": "button",
							"value": option1,

						}, 
						{
							"name": "option_"+poll_id,
							"text": option2,
							"type": "button",
							"value": option2,
						},
						{
							"name": "option_"+poll_id,
							"text": option3,
							"type": "button",
							"value": option3,
						},
						{
							"name": "option_"+poll_id,
							"text": option4,
							"type": "button",
							"value": option4,
						}							
					]

				},
				{
					"fallback":"THIS slack ",
					"callback_id": "polling_votes",
					"color": "#3AA3E3",
					"attachment_type": "default",
					"actions": [
						{
							"name": "option_"+poll_id,
							"text":option5,
							"type": "button",
							"value": option5
						}, 
						{
							"name": "option_"+poll_id,
							"text": option6,
							"type": "button",
							"value": option6
						},
						{
							"name": "option_"+poll_id,
							"text": option7,
							"type": "button",
							"value": option7,
						},
						{
							"name": "option_"+poll_id,
							"text": option8,
							"type": "button",
							"value": option8
						}
					]
				}
			]
			if resul['max_vote_user']=='' or resul['max_vote_user']=='no':
				if resul['select_options_for_users']=='':
					select_arr=[]
					options={data['user']['id']:value}
					select_arr.append(options)
					arr_json_option=json.dumps(select_arr)
					sql = "UPDATE poll SET select_options_for_users=%s WHERE poll_id=%s"
					self.cursor.execute(sql, (arr_json_option,poll_id))
					self.connection.commit()
				else:
					match=resul['select_options_for_users']
					fetch_u_op=json.loads(match)
					new_arr=[]
					request_arr=[]
					b=''
					for  user in  fetch_u_op:
						for key,val in user.items():
							print(key)
							new_arr.append(key)	

							if key==data['user']['id']:
								b={key:value}
								request_arr.append(b)
							else:
								db={key:val}
								request_arr.append(db)
					if b=='':
						b={data['user']['id']:value}
						request_arr.append(b)
					arr_json_option=json.dumps(request_arr)
					sql = "UPDATE poll SET select_options_for_users=%s WHERE poll_id=%s"
					self.cursor.execute(sql, (arr_json_option,poll_id))
					self.connection.commit()
					numofuser=len(request_arr)
			else:

				if resul['select_options_for_users']=='':
					select_arr=[]
					options={data['user']['id']:value}
					select_arr.append(options)
					arr_json_option=json.dumps(select_arr)
					sql = "UPDATE poll SET select_options_for_users=%s WHERE poll_id=%s"
					self.cursor.execute(sql, (arr_json_option,poll_id))
					self.connection.commit()
				else:
					request_arr=[]
					match=resul['select_options_for_users']
					b={data['user']['id']:value}
					request_arr.append(b)
					arr_json_option=json.dumps(request_arr)
					sql = "UPDATE poll SET select_options_for_users=%s WHERE poll_id=%s"
					self.cursor.execute(sql, (arr_json_option,poll_id))
					self.connection.commit()
					self.cursor.execute("select select_options_for_users from poll where poll_id='"+poll_id+"'")
					votes=self.cursor.fetchone()
					match=votes['select_options_for_users']
					fetch_u_op=json.loads(match)
					print(fetch_u_op)
					new_arr=[]
	
					for  user in  fetch_u_op:
						for key,val in user.items():
							print(val)
							if key==data['user']['id']:
								if val==value:
									print("jbk")
								else:
									b={key:value}
									new_arr.append(b)
							else:
								db={key:val}
								new_arr.append(db)
					arr_json_option=json.dumps(new_arr)
					sql = "UPDATE poll SET select_options_for_users=%s WHERE poll_id=%s"
					self.cursor.execute(sql, (arr_json_option,poll_id))
					self.connection.commit()
					numofuser=len(new_arr)
					
			voters_a=''
			voters_c=''
			voters_d=''
			voters_e=''
			voters_f=''
			voters_g=''
			voters_h=''
			voters_i=''
			a=0
			c=0
			d=0
			e=0
			f=0
			g=0
			h=0
			i=0
			persen=(100/numofuser)
			
			for options in request_arr:
				for key, val in options.items():
					print(val)
			
					if option1==val:
						a=a+1
						voters_a=voters_a+"<@"+key+">"				
					else:
						if option1!=None:
							if a>=1:
								a=a					
							else:
								a=0
					if option2==val:
						c=c+1
						voters_c=voters_c+"<@"+key+">"
					else:
						if option2!=None:
							if c>=1:
								c=c
							else:
								c=0
					if option3==val:
						d=d+1
						voters_d=voters_d+"<@"+key+">"
					else:
						if option3!=None:
							if d>=1:
								d=d
							else:
								d=0
					if option4==val:
						e=e+1
						voters_e=voters_e+"<@"+key+">"
					else:
						if option4!='':
							if e>=1:
								e=e
							else:
								e=0
					if option5==val:
						f=f+1
						voters_f=voters_f+"<@"+key+">"
					else:
						if option5!=None:
							if f>=1:
								f=f
							else:
								f=0					
					if option6==val:
						g=g+1
						voters_g=voters_g+"<@"+key+">"
					else:
						if option6!=None:
							if g>=1:
								g=g
							else:
								g=0
					if option7==val:
						h=h+1
						voters_h=voters_h+"<@"+key+">"
					else:
						if option7!=None:
							if h>=1:
								h=h
							else:
								h=0
					if option8==val:
						i=i+1
						voters_a=voters_a+"<@"+key+">"
					else:
						if option8!=None:
							if i>=1:
								i=i
						else:
							i=0


			print(a)
			print(c)
			print(d)
			print(e)
			persen_a=a*persen
			per_a=(round(persen_a,2))
			print(per_a)
			if per_a>75 and per_a<=100:
				attachment1={"text":"*"+option1+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_a)+"% ("+str(a)+") \n "+voters_a+""}	
				attachments_json12.append(attachment1)
			elif  per_a>65 and per_a<75:
				attachment1={"text":"*"+option1+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_a)+"% ("+str(a)+") \n "+voters_a+""}	
				attachments_json12.append(attachment1)
			elif per_a>=40 and per_a<=50:
				attachment1={"text":"*"+option1+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_a)+"% ("+str(a)+") \n "+voters_a+""}	
				attachments_json12.append(attachment1)
			elif per_a>=12 and per_a<=40:
				attachment1={"text":"*"+option1+"* \n `▆▆▆▆▆▆▆▆▆▆▆` "+str(per_a)+"% ("+str(a)+") \n "+voters_a+""}	
				attachments_json12.append(attachment1)
			elif per_a>=1 and per_a<=12:
				attachment1={"text":"*"+option1+"* \n `▆▆▆▆` "+str(per_a)+"% ("+str(a)+") \n "+voters_a+""}	
				attachments_json12.append(attachment1)
			elif per_a==0.0:
				attachment1={"text":"*"+option1+"* \n (0%)"}	
				attachments_json12.append(attachment1)
			

			persen_c=c*persen
			per_c=(round(persen_c,2))
			if per_c>=75 and per_c<=100:
				attachment2={"text":"*"+option2+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_c)+"% ("+str(c)+") \n "+voters_c+""}	
				attachments_json12.append(attachment2)
			elif  per_c>=65 and per_c<=75:
				attachment2={"text":"*"+option2+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_c)+"% ("+str(c)+") \n "+voters_c+""}	
				attachments_json12.append(attachment2)
			elif per_c>=40 and per_c<=50:
				attachment2={"text":"*"+option2+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_c)+"% ("+str(c)+") \n "+voters_c+""}	
				attachments_json12.append(attachment2)
			elif per_c>=12 and per_c<=40:
				attachment2={"text":"*"+option2+"* \n `▆▆▆▆▆▆▆▆▆▆▆` "+str(per_c)+"% ("+str(c)+") \n "+voters_c+""}	
				attachments_json12.append(attachment2)
			elif per_c>=1 and per_c<=12:
				attachment2={"text":"*"+option2+"* \n `▆▆▆▆` "+str(per_c)+"% ("+str(c)+") \n "+voters_c+""}	
				attachments_json12.append(attachment2)
			elif per_c==0.0:
				attachment2={"text":"*"+option2+"* \n (0%)"}	
				attachments_json12.append(attachment2)
			if option3!=None:
				persen_d=d*persen
				per_d=(round(persen_d,2))
				if per_d>=75 and per_d<=100:
					attachment3={"text":"*"+option3+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_d)+"% ("+str(d)+") \n "+voters_d+""}	
					attachments_json12.append(attachment3)
				elif  per_d>=65 and per_d<=75:
					attachment3={"text":"*"+option3+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_d)+"% ("+str(d)+") \n "+voters_d+""}	
					attachments_json12.append(attachment3)
				elif per_d>=40 and per_d<=50:
					attachment3={"text":"*"+option3+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_d)+"% ("+str(d)+") \n "+voters_d+""}	
					attachments_json12.append(attachment3)
				elif per_d>=12 and per_d<=40:
					attachment3={"text":"*"+option3+"* \n `▆▆▆▆▆▆▆▆▆▆▆` "+str(per_d)+"% ("+str(d)+") \n "+voters_d+""}	
					attachments_json12.append(attachment3)
				elif per_d>=1 and per_d<=12:
					attachment3={"text":"*"+option3+"* \n `▆▆▆▆` "+str(per_d)+"% ("+str(d)+") \n "+voters_d+""}	
					attachments_json12.append(attachment3)
				elif per_d==0.0:
					attachment3={"text":"*"+option3+"* \n (0%)"}	
					attachments_json12.append(attachment3)
			if option4!=None:
				persen_e=e*persen
				per_e=(round(persen_e,2))
				if per_e>=75 and per_e<=100:
					attachment4={"text":"*"+option4+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_e)+"% ("+str(e)+") \n "+voters_e+""}	
					attachments_json12.append(attachment4)
				elif  per_e>=65 and per_e<=75:
					attachment4={"text":"*"+option4+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_e)+"% ("+str(e)+") \n "+voters_e+""}	
					attachments_json12.append(attachment4)
				elif per_e>=40 and per_e<=50:
					attachment4={"text":"*"+option4+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_e)+"% ("+str(e)+") \n "+voters_e+""}	
					attachments_json12.append(attachment4)
				elif per_e>=12 and per_e<=40:
					attachment4={"text":"*"+option4+"* \n `▆▆▆▆▆▆▆▆▆▆▆` "+str(per_e)+"% ("+str(e)+") \n "+voters_e+""}	
					attachments_json12.append(attachment4)
				elif per_e>=1 and per_e<=12:
					attachment4={"text":"*"+option4+"* \n `▆▆▆▆` "+str(per_e)+"% ("+str(e)+") \n "+voters_e+""}	
					attachments_json12.append(attachment4)
				elif per_e==0.0:
					attachment4={"text":"*"+option4+"* \n (0%)"}	
					attachments_json12.append(attachment4)
			if option5!=None:
				persen_f=f*persen
				per_f=(round(persen_f,2))
				if per_f>=75 and per_f<=100:
					attachment5={"text":"*"+option5+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_f)+"% ("+str(f)+") \n "+voters_f+""}	
					attachments_json12.append(attachment5)
				elif  per_f>=65 and per_f<=75:
					attachment5={"text":"*"+option5+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_f)+"% ("+str(f)+") \n "+voters_f+""}	
					attachments_json12.append(attachment5)
				elif per_f>=40 and per_f<=50:
					attachment5={"text":"*"+option5+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_f)+"% ("+str(f)+") \n "+voters_f+""}	
					attachments_json12.append(attachment5)
				elif per_f>=12 and per_f<=40:
					attachment5={"text":"*"+option5+"* \n `▆▆▆▆▆▆▆▆▆▆▆` "+str(per_f)+"% ("+str(f)+") \n "+voters_f+""}	
					attachments_json12.append(attachment5)
				elif per_f>=1 and per_f<=12:
					attachment5={"text":"*"+option5+"* \n `▆▆▆▆` "+str(per_f)+"% ("+str(f)+") \n "+voters_f+""}	
					attachments_json12.append(attachment5)
				elif per_f==0.0:
					attachment5={"text":"*"+option5+"* \n ("+str(0)+")%)"}	
					attachments_json12.append(attachment5)
					
			if option6!=None:
				persen_g=g*persen
				per_g=(round(persen_g,2))
				if per_g>=75 and per_g<=100:
					attachment6={"text":"*"+option6+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_g)+"% ("+str(g)+") \n "+voters_g+""}	
					attachments_json12.append(attachment6)
				elif  per_g>=65 and per_g<=75:
					attachment6={"text":"*"+option6+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_g)+"% ("+str(g)+") \n "+voters_g+""}	
					attachments_json12.append(attachment6)
				elif per_g>=40 and per_g<=50:
					attachment6={"text":"*"+option6+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_g)+"% ("+str(g)+") \n "+voters_g+""}	
					attachments_json12.append(attachment6)
				elif per_g>=12 and per_g<=40:
					attachment6={"text":"*"+option6+"* \n `▆▆▆▆▆▆▆▆▆▆▆` "+str(per_g)+"% ("+str(g)+") \n "+voters_g+""}	
					attachments_json12.append(attachment6)
				elif per_g>=1 and per_g<=12:
					attachment6={"text":"*"+option6+"* \n `▆▆▆▆` "+str(per_g)+"% ("+str(g)+") \n "+voters_g+""}	
					attachments_json12.append(attachment6)
				elif per_g==0.0:
					attachment6={"text":"*"+option6+"* \n ("+str(0)+")%)"}	
					attachments_json12.append(attachment6)
			if option7!=None:
				persen_h=h*persen
				per_h=(round(persen_h,2))
				if per_h>=75 and per_h<=100:
					attachment7={"text":"*"+option7+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_h)+"% ("+str(h)+") \n "+voters_h+""}	
					attachments_json12.append(attachment7)
				elif  per_h>=65 and per_h<=75:
					attachment7={"text":"*"+option7+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_h)+"% ("+str(h)+") \n "+voters_h+""}	
					attachments_json12.append(attachment7)
				elif per_h>=40 and per_h<=50:
					attachment7={"text":"*"+option7+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_h)+"% ("+str(h)+") \n "+voters_h+""}	
					attachments_json12.append(attachment7)
				elif per_h>=12 and per_h<=40:
					attachment7={"text":"*"+option7+"* \n `▆▆▆▆▆▆▆▆▆▆▆` "+str(per_h)+"% ("+str(h)+") \n "+voters_h+""}	
					attachments_json12.append(attachment7)
				elif per_h>=1 and per_h<=12:
					attachment7={"text":"*"+option7+"* \n `▆▆▆▆` "+str(per_h)+"% ("+str(h)+") \n "+voters_h+""}	
					attachments_json12.append(attachment7)
				elif per_h==0.0:
					attachment7={"text":"*"+option7+"* \n ("+str(0)+")%)"}	
					attachments_json12.append(attachment7)
			if option8!=None:
				persen_i=i*persen
				per_i=(round(persen_i,2))
				if per_i>=75 and per_i<=100:
					attachment8={"text":"*"+option8+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_i)+"% ("+str(i)+") \n "+voters_i+""}	
					attachments_json12.append(attachment8)
				elif  per_i>=65 and per_i<=75:
					attachment8={"text":"*"+option8+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_i)+"% ("+str(i)+") \n "+voters_i+""}	
					attachments_json12.append(attachment8)
				elif per_i>=40 and per_i<=50:
					attachment8={"text":"*"+option8+"* \n `▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆▆` "+str(per_i)+"% ("+str(i)+") \n "+voters_i+""}	
					attachments_json12.append(attachment8)
				elif per_i>=12 and per_i<=40:
					attachment8={"text":"*"+option8+"* \n `▆▆▆▆▆▆▆▆▆▆▆` "+str(per_i)+"% ("+str(i)+") \n "+voters_i+""}	
					attachments_json12.append(attachment8)
				elif per_i>=1 and per_i<=12:
					attachment8={"text":"*"+option8+"* \n `▆▆▆▆` "+str(per_i)+"% ("+str(i)+") \n "+voters_i+""}	
					attachments_json12.append(attachment8)
				elif per_i==0.0:
					attachment8={"text":"*"+option7+"* \n ("+str(0)+")%)"}	
					attachments_json12.append(attachment8)
			attachment9={"text":"*Total Votes* \n "+str(numofuser)+""}	
			attachments_json12.append(attachment9)
			ts=data['message_ts']
			slack_client.api_call("chat.update",channel=data['channel']['id'],attachments=attachments_json12,ts=ts)
			return Response(''),200
		
		elif callback_id=="polling_submit":
			print(data)
			ts=data['message_ts']
			print(ts)
			action_name=data['actions'][0]['name']
			if "pollsubmit_" in action_name:
				poll_id=action_name.split("pollsubmit_",1)[1]
				self.connection_start()
				self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
				resul=self.cursor.fetchone()
				old_option=resul['poll_option']
				qus=resul['poll_tittel']
				fetch_optin=json.loads(old_option)
				full_option=[]
				i=1
				for option_data in fetch_optin:
					o={"option"+str(i):option_data['option']}
					full_option.append(o)
					i=i+1	
				length=len(full_option)
				option1=full_option[0]['option1']
				option2=full_option[1]['option2']
				if length > 2:
					option3=full_option[2]['option3']
				else:
					option3=None
				if length > 3:
					option4=full_option[3]['option4']
				else:
					option4=None
				if length > 4:
					option5=full_option[4]['option5']
				else:
					option5=None
				if length > 5:
					option6=full_option[5]['option6']
				else:
					option6=None
				if length > 6:
					option7=full_option[6]['option7']
				else:
					option7=None
				if length > 7:
					option8=full_option[7]['option8']
				else:
					option8=None
				if data['channel']['name']=="directmessage" or data['channel']['name']=="privategroup":
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_votes",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							"fallback":"THIS slack ",
							"callback_id": "polling_votes",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5
								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8
								}
							]
						},
						{
							"fallback":"THIS slack ",
							"callback_id": "polling_votes",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "delete_"+poll_id,
									"text":"DELETE",
									"type": "button",
									"value": "delete"
								}
							]
						}
					]	
					slack_client.api_call('chat.postMessage',channel=data['channel']['id'],attachments=attachments_json12)
					return Response(''),200
				
				else:
					slack_client.api_call("chat.delete",channel=data['channel']['id'],ts=ts)
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_votes",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							"fallback":"THIS slack ",
							"callback_id": "polling_votes",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5
								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8
								}
							]
						}
					]
					if resul['send']=='':
						slack_client.api_call('chat.postMessage',channel=data['channel']['id'],attachments=attachments_json12)
					else:
						slack_client.api_call('chat.postMessage',channel=resul['send'],attachments=attachments_json12)


					return Response(''),200
			elif "polladvanceoptions_" in action_name:
				poll_id=action_name.split("polladvanceoptions_",1)[1]

				name=data['channel']['name']
				self.connection_start()
				self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
				resul=self.cursor.fetchone()
				old_option=resul['poll_option']
				qus=resul['poll_tittel']
				ts=data['message_ts']
				fetch_optin=json.loads(old_option)
				option_delete=[]
				i=1
				for option_data in fetch_optin:
					o={"option"+str(i):option_data['option']}
					option_delete.append(o)
					i=i+1
				print(option_delete)
				option1=option_delete[0]['option1']
				option2=option_delete[1]['option2']
				length=len(option_delete)
				if length > 2:
					option3=option_delete[2]['option3']
					print(option3)
				else:
					option3=None
				if length > 3:
					option4=option_delete[3]['option4'] 
					print(option4)
				else: 
					option4=None
				if length > 4:
					option5=option_delete[4]['option5'] 
					print(option5)
				else: 
					option5=None
				if length > 5:
					option6=option_delete[5]['option6'] 
					print(option6)
				else: 
					option6=None
				
				if length > 6:
					option7=option_delete[6]['option7'] 
					print(option7)
				else: 
					option7=None
				if length >7:
					option8=option_delete[7]['option8'] 
					print(option8)
				else: 
					option8=None
				if length==8:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								}							
							]

						}
					]
				else:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								},
								{
									"name": "addoption_"+poll_id,
									"text": "+ Add Option",
									"type": "button",
									"value": "Addoption",
								}
							]

						}
					]
				if name!="directmessage" and name!="privategroup" :
					attachment1={
									"fallback":"THIS slack ",
									"callback_id": "polling_recurring",
									"color": "#3AA3E3",
									"attachment_type": "default",
									"actions": [
										{
											"name": "pollrimender_"+poll_id,
											
											"type": "select",
											"value": "selectpoll",
											"options": [
												{
													"text": "one time (recurring)",
													"value": "one_time"
												},
												{
													"text": "every time (recurring)",
													"value": "every time"
												},
												{
													"text": "every week (recurring)",
													"value": "every_week"
												},
												{
													"text": "every 2 weeks (recurring)",
													"value": "every_2weeks"
												},
												{
													"text": "every 3 weeks (recurring)",
													"value": "every_3weeks"
												},
												{
													"text": "every month (recurring)",
													"value": "every_month"
												},
												{
													"text": "every 3 months (recurring)",
													"value": "every_3month"
												},
												{
													"text": "every 6 months (recurring)",
													"value": "every_6month"
												},
												
											],
											"selected_options": [
			                        			{
			                            			"text": "one time (recurring)",
													"value": "one_time"
			                       			 	}
			                    			]
										}
										
									]
								}
					attachments_json12.append(attachment1)
				
				attachment3={"text":"*Date/Time*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
				attachments_json12.append(attachment3)				
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
				attachments_json12.append(attachment4)
				if resul['send']=='':
					attachment5={"text":"*Poll Audience*  \n <#"+data['channel']['id']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				else:
					attachment5={"text":"*Poll Audience*  \n <#"+resul['send']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				attachment2={"text": " *SUBMIT / CANCEL* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll","style":"danger"}]}
				attachments_json12.append(attachment2)
				message= {'text':"<@"+data['user']['id']+"> used `/Event Manage bot`",'attachments':attachments_json12 ,'response_type': 'ephemeral', 'replace_original': True}
				response_url=data['response_url']
				request_response = self.req_response(response_url , message)
				return Response(''),200
		elif callback_id=="poll_audience":
			print(data)
			channel1=data['channel']['name']
			channel=data['actions'][0]['selected_options'][0]['value']
			action_name=data['actions'][0]['name']
			poll_id=action_name.split("pollchannel_",1)[1]
			print(poll_id)
			self.connection_start()
			sql = "UPDATE poll SET send=%s WHERE poll_id=%s"
			self.cursor.execute(sql, (channel,poll_id))
			self.connection.commit()
			self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
			resul=self.cursor.fetchone()
			print(resul)
			old_option=resul['poll_option']
			qus=resul['poll_tittel']
			fetch_optin=json.loads(old_option)
			option_delete=[]
			i=1
			for option_data in fetch_optin:
				o={"option"+str(i):option_data['option']}
				option_delete.append(o)
				i=i+1
			print(option_delete)
			option1=option_delete[0]['option1']
			option2=option_delete[1]['option2']
			length=len(option_delete)
			if length > 2:
				option3=option_delete[2]['option3']
				print(option3)
			else:
				option3=None
			if length > 3:
				option4=option_delete[3]['option4'] 
				print(option4)
			else: 
				option4=None
			if length > 4:
				option5=option_delete[4]['option5'] 
				print(option5)
			else: 
				option5=None
			if length > 5:
				option6=option_delete[5]['option6'] 
				print(option6)
			else: 
				option6=None
			
			if length > 6:
				option7=option_delete[6]['option7'] 
				print(option7)
			else: 
				option7=None
			if length >7:
				option8=option_delete[7]['option8'] 
				print(option8)
			else: 
				option8=None
			if length==8:
				attachments_json12=[
					{
						"text": " *"+qus+"* ",
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option1,
								"type": "button",
								"value": option1,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option2,
								"type": "button",
								"value": option2,
							},
							{
								"name": "option_"+poll_id,
								"text": option3,
								"type": "button",
								"value": option3,
							},
							{
								"name": "option_"+poll_id,
								"text": option4,
								"type": "button",
								"value": option4,
							}							
						]

					},
					{
						
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option5,
								"type": "button",
								"value": option5,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option6,
								"type": "button",
								"value": option6,
							},
							{
								"name": "option_"+poll_id,
								"text": option7,
								"type": "button",
								"value": option7,
							},
							{
								"name": "option_"+poll_id,
								"text": option8,
								"type": "button",
								"value": option8,
							}							
						]

					}
				]
			else:

				attachments_json12=[
					{
						"text": " *"+qus+"* ",
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option1,
								"type": "button",
								"value": option1,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option2,
								"type": "button",
								"value": option2,
							},
							{
								"name": "option_"+poll_id,
								"text": option3,
								"type": "button",
								"value": option3,
							},
							{
								"name": "option_"+poll_id,
								"text": option4,
								"type": "button",
								"value": option4,
							}							
						]

					},
					{
						
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option5,
								"type": "button",
								"value": option5,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option6,
								"type": "button",
								"value": option6,
							},
							{
								"name": "option_"+poll_id,
								"text": option7,
								"type": "button",
								"value": option7,
							},
							{
								"name": "option_"+poll_id,
								"text": option8,
								"type": "button",
								"value": option8,
							},
							{
								"name": "addoption_"+poll_id,
								"text": "+ Add Option",
								"type": "button",
								"value": "Addoption",
							}
						]

					}
				]
			if channel1!="directmessage" or channel1!="privategroup":
				if resul['poll_reminder']!='':
					attachment1={
									"fallback":"THIS slack ",
									"callback_id": "polling_recurring",
									"color": "#3AA3E3",
									"attachment_type": "default",
									"actions": [
										{
											"name": "pollrimender_"+poll_id,
											
											"type": "select",
											"value": "selectpoll",
											"options": [
												{
													"text": "one time (recurring)",
													"value": "one_time"
												},
												{
													"text": "every time (recurring)",
													"value": "every time"
												},
												{
													"text": "every week (recurring)",
													"value": "every_week"
												},
												{
													"text": "every 2 weeks (recurring)",
													"value": "every_2weeks"
												},
												{
													"text": "every 3 weeks (recurring)",
													"value": "every_3weeks"
												},
												{
													"text": "every month (recurring)",
													"value": "every_month"
												},
												{
													"text": "every 3 months (recurring)",
													"value": "every_3month"
												},
												{
													"text": "every 6 months (recurring)",
													"value": "every_6month"
												},
												
											],
											"selected_options": [
			                        			{
			                            			"text": resul['poll_reminder'],
			                            			"value": resul['poll_reminder'],
			                       			 	}
			                    			]
										}
										
									]
								}
					attachments_json12.append(attachment1)
				else:
					attachment1={
									"fallback":"THIS slack ",
									"callback_id": "polling_recurring",
									"color": "#3AA3E3",
									"attachment_type": "default",
									"actions": [
										{
											"name": "pollrimender_"+poll_id,
											
											"type": "select",
											"value": "selectpoll",
											"options": [
												{
													"text": "one time (recurring)",
													"value": "one_time"
												},
												{
													"text": "every time (recurring)",
													"value": "every time"
												},
												{
													"text": "every week (recurring)",
													"value": "every_week"
												},
												{
													"text": "every 2 weeks (recurring)",
													"value": "every_2weeks"
												},
												{
													"text": "every 3 weeks (recurring)",
													"value": "every_3weeks"
												},
												{
													"text": "every month (recurring)",
													"value": "every_month"
												},
												{
													"text": "every 3 months (recurring)",
													"value": "every_3month"
												},
												{
													"text": "every 6 months (recurring)",
													"value": "every_6month"
												},
												
											],
											"selected_options": [
			                        			{
			                            			"text": "one time (recurring)",
													"value": "one_time"
			                       			 	}
			                    			]
										}
										
									]
								}
					attachments_json12.append(attachment1)
			if resul['poll_date']=='' and resul['poll_time']=='':
				attachment3={"text":"*Date/Time*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
				attachments_json12.append(attachment3)
			elif resul['poll_date']!='' and resul['poll_time']=='': 
				attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
				attachments_json12.append(attachment3)
			elif resul['poll_date']=='' and resul['poll_time']!='': 
				attachment3={"text":"*Date/Time* \n Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
				attachments_json12.append(attachment3)
			elif resul['poll_date']!='' and resul['poll_time']!='': 
				attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"* Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
				attachments_json12.append(attachment3)
			if resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='yes' :
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger"}]}
				attachments_json12.append(attachment4)
			elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='no':
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
				attachments_json12.append(attachment4)
			elif resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='no':
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger",}]}
				attachments_json12.append(attachment4)
			elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='yes':
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
				attachments_json12.append(attachment4)
			elif resul['allow_user_add_option']=='' and resul['max_vote_user']=='':
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
				attachments_json12.append(attachment4)
			if resul['send']=='':
				attachment5={"text":"*Poll Audience*  \n <#"+channel+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
				attachments_json12.append(attachment5)
			else:
				attachment5={"text":"*Poll Audience*  \n <#"+resul['send']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
				attachments_json12.append(attachment5)
			attachment2={"text": " *SUBMIT / CANCEL* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll","style":"danger"}]}
			attachments_json12.append(attachment2)
			response_url=data['response_url']
			message= {'text':"<@"+data['user']['id']+"> used `/Event Manage bot`",'attachments':attachments_json12 ,'response_type': 'ephemeral','replace_original': True}
			request_response = self.req_response(response_url , message)
			return Response(''),200




		elif callback_id=="polling_question":
			channel_id=data['channel']['id']
			print(data)
			print('iubkbkbkbkjb')
			name=data['channel']['name']
			print(name)
			flag = False
			poll_info = []
			for key,value in data['submission'].items():
				if 'question1_' in key:
					flag = True
					poll_info = key
			if flag:
				poll_user = poll_info.split("question1_",1)[1]
				qus= data['submission']['question1_'+poll_user]
				option_arr=[]
				option1=data['submission']['option1']
				option2=data['submission']['option2']
				option3=data['submission']['option3']
				option4=data['submission']['option4']
				option_arr.append(option1)
				option_arr.append(option2)
				option_arr.append(option3)
				option_arr.append(option4)
				poll_database=[]
				print(option_arr)
				for conver in option_arr:
					if conver==None:
						print("no data")
					else:
						b={"option":conver} 
						poll_database.append(b)
				dump=json.dumps(poll_database)
				self.connection_start()
				sql = "INSERT INTO poll (`poll_tittel`, `poll_user_id` ,`poll_channel_id`,`poll_option`)VALUES(%s, %s, %s,%s)"
				self.cursor.execute(sql, (qus,poll_user,channel_id,dump))
				self.connection.commit()
				self.cursor.execute("select `poll_id`  from poll where poll_tittel='"+qus+"' and poll_user_id='"+poll_user+"' and poll_channel_id='"+channel_id+"'")
				resul=self.cursor.fetchone()
				if resul:
					poll_id=str(resul['poll_id'])
					print(resul)
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,
								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								},
								{
									"name": "addoption_"+poll_id,
									"text": "+ Add Option",
									"type": "button",
									"value": "Addoption",
								}
							]
						}
					]	
					if name!="directmessage" and name!="privategroup" :
						attachment1={
										"fallback":"THIS slack ",
										"callback_id": "polling_recurring",
										"color": "#3AA3E3",
										"attachment_type": "default",
										"actions": [
											{
												"name": "pollrimender_"+poll_id,
												
												"type": "select",
												"value": "selectpoll",
												"options": [
													{
														"text": "one time (recurring)",
														"value": "one_time"
													},
													{
														"text": "every time (recurring)",
														"value": "every time"
													},
													{
														"text": "every week (recurring)",
														"value": "every_week"
													},
													{
														"text": "every 2 weeks (recurring)",
														"value": "every_2weeks"
													},
													{
														"text": "every 3 weeks (recurring)",
														"value": "every_3weeks"
													},
													{
														"text": "every month (recurring)",
														"value": "every_month"
													},
													{
														"text": "every 3 months (recurring)",
														"value": "every_3month"
													},
													{
														"text": "every 6 months (recurring)",
														"value": "every_6month"
													},
													
												],
												"selected_options": [
				                        			{
				                            			"text": "one time (recurring)",
				                            			"value": "one_time"
				                       			 	}
				                    			]
											}
											
										]
									}
						attachments_json12.append(attachment1)
					attachment2={"text": " *SUBMIT* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "polladvanceoptions_"+poll_id,"text":"Advanced Option","type": "button","value": "poll_advance_option",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll",}]}
					attachments_json12.append(attachment2)
					response_url=data['response_url']
					res=slack_client.api_call("chat.postEphemeral",channel=data['channel']['id'], user=data['user']['id'],attachments= attachments_json12,text="<@"+poll_user+"> used `/Event Manage bot`",as_user=False)
					print(res)
					message_ts=res['message_ts']
					sql = "UPDATE poll SET message_ts=%s WHERE poll_id=%s"
					self.cursor.execute(sql, (message_ts,poll_id))
					self.connection.commit()
				return Response(''),200
		elif  callback_id=="polling_option":
				poll_action_name=data['actions'][0]['name']
				
				if "addoption_" in poll_action_name:
					poll_id=poll_action_name.split("addoption_",1)[1]
					slack_client.api_call('dialog.open', trigger_id=data['trigger_id'],channel=data['channel']['id'],
						dialog={
									"trigger_id":data['trigger_id'],
									"callback_id": "polling_add_option_"+poll_id,
									"title": "POLL",
									"submit_label": "Request",
									"elements": [
										{
											"type": "text",
											"label": "Option 1:",
											"name":"option1",
											"placeholder": "Enter 1st option",
											"optional":True
										},
										{
											"type": "text",
											"label": "Option 2:",
											"name":"option2",
											"placeholder": "Enter 2st option",
											"optional":True
										},
										{
											"type": "text",
											"label": "Option 3:",
											"name":"option3",
											"placeholder": "Enter 3st option",
											"optional":True
										},
										{
											"type": "text",
											"label": "Option 4:",
											"name":"option4",
											"placeholder": "Enter 4st option",
											"optional":True
										}
									 ]
								})
					return Response(''),200
				
				elif "option_" in poll_action_name:
					poll_id=poll_action_name.split("option_",1)[1]
					option_value=data['actions'][0]['value']
					slack_client.api_call('dialog.open', trigger_id=data['trigger_id'],channel=data['channel']['id'],
							dialog={
										"trigger_id":data['trigger_id'],
										"callback_id": "polling_edit_option_"+poll_id,
										"title": "POLL OPTION EDIT",
										"submit_label": "Request",
										"elements": [
											{
											"type": "text",
											"label": "Edir option:",
											"value":option_value,
											"name": "option_"+option_value,
											"placeholder": "Enter 1st question"
											}
										]
									})
					return Response(''),200

		elif "polling_add_option_" in callback_id:
			channel_id=data['channel']['id']
			name=data['channel']['name']
			print(data)
			poll_id=callback_id.split("polling_add_option_",1)[1]
			self.connection_start()
			self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
			resul=self.cursor.fetchone()
			old_option=resul['poll_option']
			qus=resul['poll_tittel']
			ts=resul['message_ts']
			print(ts)
			fetch_optin=json.loads(old_option)
			show_array=[]
			option_delete=[]
			i=1
			for option_data in fetch_optin:
				db={"option":option_data['option']}
				show_array.append(db)
				o={"option"+str(i):option_data['option']}
				option_delete.append(o)
				i=i+1	
			option_arr=[]
			option5=data['submission']['option1']
			option6=data['submission']['option2']
			option7=data['submission']['option3']
			option8=data['submission']['option4']
			option_arr.append(option5)
			option_arr.append(option6)
			option_arr.append(option7)
			option_arr.append(option8)
			for conver in option_arr:
				if conver==None:
					print("no data")
				else:
					b={"option":conver} 
					show_array.append(b)
			db_option=json.dumps(show_array)
			sql = "UPDATE poll SET poll_option=%s WHERE poll_id=%s"
			self.cursor.execute(sql, (db_option,poll_id))
			self.connection.commit()
			length=len(option_delete)
			option1=option_delete[0]['option1']
			option2=option_delete[1]['option2']
			if length > 2:
				option3=option_delete[2]['option3']
			else:
				option3=None
			if length > 3:
				option4=option_delete[3]['option4']
			else:
				option4=None
			length2=len(show_array)
			if length2==8:
				attachments_json12=[
					{
						"text": " *"+qus+"* ",
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option1,
								"type": "button",
								"value": option1,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option2,
								"type": "button",
								"value": option2,
							},
							{
								"name": "option_"+poll_id,
								"text": option3,
								"type": "button",
								"value": option3,
							},
							{
								"name": "option_"+poll_id,
								"text": option4,
								"type": "button",
								"value": option4,
							}							
						]

					},
					{
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option5,
								"type": "button",
								"value": option5
							}, 
							{
								"name": "option_"+poll_id,
								"text": option6,
								"type": "button",
								"value": option6
							},
							{
								"name": "option_"+poll_id,
								"text": option7,
								"type": "button",
								"value": option7,
							},
							{
								"name": "option_"+poll_id,
								"text": option8,
								"type": "button",
								"value": option8
							}
						]
					},
				]	
			else:
				attachments_json12=[
					{
						"text": " *"+qus+"* ",
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option1,
								"type": "button",
								"value": option1,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option2,
								"type": "button",
								"value": option2,
							},
							{
								"name": "option_"+poll_id,
								"text": option3,
								"type": "button",
								"value": option3,
							},
							{
								"name": "option_"+poll_id,
								"text": option4,
								"type": "button",
								"value": option4,
							}							
						]

					},
					{
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option5,
								"type": "button",
								"value": option5
							}, 
							{
								"name": "option_"+poll_id,
								"text": option6,
								"type": "button",
								"value": option6
							},
							{
								"name": "option_"+poll_id,
								"text": option7,
								"type": "button",
								"value": option7,
							},
							{
								"name": "option_"+poll_id,
								"text": option8,
								"type": "button",
								"value": option8
							},
							{
								"name": "addoption_"+poll_id,
								"text": "+ Add Option",
								"type": "button",
								"value": "Addoption",
							}
						]
					},
				]	
			res=slack_client.api_call("chat.delete",channel=channel_id,ts=ts)
			print(res)
			if name!="directmessage" and  name!="privategroup":
				if resul['poll_reminder']=='':
					attachment1={
									"fallback":"THIS slack ",
									"callback_id": "polling_recurring",
									"color": "#3AA3E3",
									"attachment_type": "default",
									"actions": [
										{
											"name": "pollrimender_"+poll_id,
											
											"type": "select",
											"value": "selectpoll",
											"options": [
												{
													"text": "one time (recurring)",
													"value": "one_time"
												},
												{
													"text": "every time (recurring)",
													"value": "every time"
												},
												{
													"text": "every week (recurring)",
													"value": "every_week"
												},
												{
													"text": "every 2 weeks (recurring)",
													"value": "every_2weeks"
												},
												{
													"text": "every 3 weeks (recurring)",
													"value": "every_3weeks"
												},
												{
													"text": "every month (recurring)",
													"value": "every_month"
												},
												{
													"text": "every 3 months (recurring)",
													"value": "every_3month"
												},
												{
													"text": "every 6 months (recurring)",
													"value": "every_6month"
												},
												
											],
											"selected_options": [
			                        			{
			                            			"text": "one time (recurring)",
			                            			"value": "one_time"
			                       			 	}
			                    			]
										}
										
									]
								}
					attachments_json12.append(attachment1)	
				else:
					attachment1={
									"fallback":"THIS slack ",
									"callback_id": "polling_recurring",
									"color": "#3AA3E3",
									"attachment_type": "default",
									"actions": [
										{
											"name": "pollrimender_"+poll_id,
											
											"type": "select",
											"value": "selectpoll",
											"options": [
												{
													"text": "one time (recurring)",
													"value": "one_time"
												},
												{
													"text": "every time (recurring)",
													"value": "every time"
												},
												{
													"text": "every week (recurring)",
													"value": "every_week"
												},
												{
													"text": "every 2 weeks (recurring)",
													"value": "every_2weeks"
												},
												{
													"text": "every 3 weeks (recurring)",
													"value": "every_3weeks"
												},
												{
													"text": "every month (recurring)",
													"value": "every_month"
												},
												{
													"text": "every 3 months (recurring)",
													"value": "every_3month"
												},
												{
													"text": "every 6 months (recurring)",
													"value": "every_6month"
												},
												
											],
											"selected_options": [
			                        			{
			                            			"text": resul['poll_reminder'],
			                            			"value": resul['poll_reminder']
			                       			 	}
			                    			]
										}
										
									]
								}
					attachments_json12.append(attachment1)
					if resul['poll_date']=='' and resul['poll_time']=='':
						attachment3={"text":"*Date/Time*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
						attachments_json12.append(attachment3)
					elif resul['poll_date']!='' and resul['poll_time']=='': 
						attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
						attachments_json12.append(attachment3)
					elif resul['poll_date']=='' and resul['poll_time']!='': 
						attachment3={"text":"*Date/Time* \n Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
						attachments_json12.append(attachment3)
					elif resul['poll_date']!='' and resul['poll_time']!='': 
						attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"* Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
						attachments_json12.append(attachment3)
					if resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='yes' :
						attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger"}]}
						attachments_json12.append(attachment4)
					elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='no':
						attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
						attachments_json12.append(attachment4)
					elif resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='no':
						attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger",}]}
						attachments_json12.append(attachment4)
					elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='yes':
						attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
						attachments_json12.append(attachment4)
					elif resul['allow_user_add_option']=='' and resul['max_vote_user']=='':
						attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
						attachments_json12.append(attachment4)
					if resul['send']=='':
						attachment5={"text":"*Poll Audience*  \n <#"+data['channel']['id']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
						attachments_json12.append(attachment5)
					else:
						attachment5={"text":"*Poll Audience*  \n <#"+resul['send']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
						attachments_json12.append(attachment5)


			attachment2={"text": " *SUBMIT* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "polladvanceoptions_"+poll_id,"text":"Advanced Option","type": "button","value": "poll_advance_option",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll",}]}
			attachments_json12.append(attachment2)
			slack_client.api_call("chat.postEphemeral",channel=data['channel']['id'], user=data['user']['id'],attachments= attachments_json12,text="<@"+data['user']['id']+"> used `/Event Manage bot`")
			return Response(''),200
		elif callback_id=="polling_recurring":
			print(data)
			value=data['actions'][0]['selected_options'][0]['value']
			name=data['actions'][0]['name']
			poll_id=name.split("pollrimender_",1)[1]
			channel1=data['channel']['name']
			self.connection_start()
			sql = "UPDATE poll SET poll_reminder=%s WHERE poll_id=%s"
			self.cursor.execute(sql, (value,poll_id))
			self.connection.commit()
			self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
			resul=self.cursor.fetchone()
			print(resul)
			old_option=resul['poll_option']
			qus=resul['poll_tittel']
			ts=data['message_ts']
			fetch_optin=json.loads(old_option)
			option_delete=[]
			i=1
			for option_data in fetch_optin:
				o={"option"+str(i):option_data['option']}
				option_delete.append(o)
				i=i+1
			print(option_delete)
			option1=option_delete[0]['option1']
			option2=option_delete[1]['option2']
			length=len(option_delete)
			if length > 2:
				option3=option_delete[2]['option3']
				print(option3)
			else:
				option3=None
			if length > 3:
				option4=option_delete[3]['option4'] 
				print(option4)
			else: 
				option4=None
			if length > 4:
				option5=option_delete[4]['option5'] 
				print(option5)
			else: 
				option5=None
			if length > 5:
				option6=option_delete[5]['option6'] 
				print(option6)
			else: 
				option6=None
			
			if length > 6:
				option7=option_delete[6]['option7'] 
				print(option7)
			else: 
				option7=None
			if length >7:
				option8=option_delete[7]['option8'] 
				print(option8)
			else: 
				option8=None
			if length==8:
				attachments_json12=[
					{
						"text": " *"+qus+"* ",
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option1,
								"type": "button",
								"value": option1,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option2,
								"type": "button",
								"value": option2,
							},
							{
								"name": "option_"+poll_id,
								"text": option3,
								"type": "button",
								"value": option3,
							},
							{
								"name": "option_"+poll_id,
								"text": option4,
								"type": "button",
								"value": option4,
							}							
						]

					},
					{
						
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option5,
								"type": "button",
								"value": option5,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option6,
								"type": "button",
								"value": option6,
							},
							{
								"name": "option_"+poll_id,
								"text": option7,
								"type": "button",
								"value": option7,
							},
							{
								"name": "option_"+poll_id,
								"text": option8,
								"type": "button",
								"value": option8,
							}							
						]

					}
				]
			else:
				attachments_json12=[
					{
						"text": " *"+qus+"* ",
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option1,
								"type": "button",
								"value": option1,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option2,
								"type": "button",
								"value": option2,
							},
							{
								"name": "option_"+poll_id,
								"text": option3,
								"type": "button",
								"value": option3,
							},
							{
								"name": "option_"+poll_id,
								"text": option4,
								"type": "button",
								"value": option4,
							}							
						]

					},
					{
						
						"fallback":"THIS slack ",
						"callback_id": "polling_option",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "option_"+poll_id,
								"text":option5,
								"type": "button",
								"value": option5,

							}, 
							{
								"name": "option_"+poll_id,
								"text": option6,
								"type": "button",
								"value": option6,
							},
							{
								"name": "option_"+poll_id,
								"text": option7,
								"type": "button",
								"value": option7,
							},
							{
								"name": "option_"+poll_id,
								"text": option8,
								"type": "button",
								"value": option8,
							},
							{
								"name": "addoption_"+poll_id,
								"text": "+ Add Option",
								"type": "button",
								"value": "Addoption",
							}
						]

					}
				]
			if channel1!="directmessage" or channel1!="privategroup":
				attachment1={
								"fallback":"THIS slack ",
								"callback_id": "polling_recurring",
								"color": "#3AA3E3",
								"attachment_type": "default",
								"actions": [
									{
										"name": "pollrimender_"+poll_id,
										
										"type": "select",
										"value": "selectpoll",
										"options": [
											{
												"text": "one time (recurring)",
												"value": "one_time"
											},
											{
												"text": "every time (recurring)",
												"value": "every time"
											},
											{
												"text": "every week (recurring)",
												"value": "every_week"
											},
											{
												"text": "every 2 weeks (recurring)",
												"value": "every_2weeks"
											},
											{
												"text": "every 3 weeks (recurring)",
												"value": "every_3weeks"
											},
											{
												"text": "every month (recurring)",
												"value": "every_month"
											},
											{
												"text": "every 3 months (recurring)",
												"value": "every_3month"
											},
											{
												"text": "every 6 months (recurring)",
												"value": "every_6month"
											},
											
										],
										"selected_options": [
		                        			{
		                            			"text": value,
		                            			"value": value,
		                       			 	}
		                    			]
									}
									
								]
							}
				attachments_json12.append(attachment1)
			if resul['poll_date']=='' and resul['poll_time']=='':
				attachment3={"text":"*Date/Time*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
				attachments_json12.append(attachment3)
			elif resul['poll_date']!='' and resul['poll_time']=='': 
				attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
				attachments_json12.append(attachment3)
			elif resul['poll_date']=='' and resul['poll_time']!='': 
				attachment3={"text":"*Date/Time* \n Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
				attachments_json12.append(attachment3)
			elif resul['poll_date']!='' and resul['poll_time']!='': 
				attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"* Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
				attachments_json12.append(attachment3)
			if resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='yes' :
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger"}]}
				attachments_json12.append(attachment4)
			elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='no':
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
				attachments_json12.append(attachment4)
			elif resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='no':
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger",}]}
				attachments_json12.append(attachment4)
			elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='yes':
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
				attachments_json12.append(attachment4)
			elif resul['allow_user_add_option']=='' and resul['max_vote_user']=='':
				attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
				attachments_json12.append(attachment4)
			if resul['send']=='':
				attachment5={"text":"*Poll Audience*  \n <#"+data['channel']['id']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
				attachments_json12.append(attachment5)
			else:
				attachment5={"text":"*Poll Audience*  \n <#"+resul['send']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
				attachments_json12.append(attachment5)
			attachment2={"text": " *SUBMIT / CANCEL* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll","style":"danger"}]}
			attachments_json12.append(attachment2)
			response_url=data['response_url']
			message= {'text':"<@"+data['user']['id']+"> used `/Event Manage bot`",'attachments':attachments_json12 ,'response_type': 'ephemeral','ts':ts,'replace_original': True}
			request_response = self.req_response(response_url , message)
			return Response(''),200
		elif callback_id=="poll_date_time" :
			print(data) 
			name=data['actions'][0]['name']
			if "polldate_" in name:
				poll_date=data['actions'][0]['selected_options'][0]['value']
				poll_id=name.split("polldate_",1)[1]
				ts=data['message_ts']
				self.connection_start()
				sql = "UPDATE poll SET poll_date=%s WHERE poll_id=%s"
				self.cursor.execute(sql, (poll_date,poll_id))
				self.connection.commit()
				self.connection_start()
				self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
				resul=self.cursor.fetchone()
				print("resul")
				old_option=resul['poll_option']
				qus=resul['poll_tittel']
				value=resul['poll_reminder']
				fetch_optin=json.loads(old_option)
				option_delete=[]
				i=1
				for option_data in fetch_optin:
					o={"option"+str(i):option_data['option']}
					option_delete.append(o)
					i=i+1
				print(option_delete)
				option1=option_delete[0]['option1']
				option2=option_delete[1]['option2']
				length=len(option_delete)
				if length > 2:
					option3=option_delete[2]['option3']
					print(option3)
				else:
					option3=None
				if length > 3:
					option4=option_delete[3]['option4'] 
					print(option4)
				else: 
					option4=None
				if length > 4:
					option5=option_delete[4]['option5'] 
					print(option5)
				else: 
					option5=None
				if length > 5:
					option6=option_delete[5]['option6'] 
					print(option6)
				else: 
					option6=None
				
				if length > 6:
					option7=option_delete[6]['option7'] 
					print(option7)
				else: 
					option7=None
				if length >7:
					option8=option_delete[7]['option8'] 
					print(option8)
				else: 
					option8=None
				if length==8:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								}							
							]
						}
					]	
				else:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]
						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								},
								{
									"name": "addoption_"+poll_id,
									"text": "+ Add Option",
									"type": "button",
									"value": "Addoption",
								}				
							]
						}
					]
				if data['channel']['name']!='directmessage' and  data['channel']['name']!='privategroup':	
					print("kdejfkj")
					attachment1={
									"fallback":"THIS slack ",
									"callback_id": "polling_recurring",
									"color": "#3AA3E3",
									"attachment_type": "default",
									"actions": [
										{
											"name": "pollrimender_"+poll_id,
											
											"type": "select",
											"value": "selectpoll",
											"options": [
												{
													"text": "one time (recurring)",
													"value": "one_time"
												},
												{
													"text": "every time (recurring)",
													"value": "every time"
												},
												{
													"text": "every week (recurring)",
													"value": "every_week"
												},
												{
													"text": "every 2 weeks (recurring)",
													"value": "every_2weeks"
												},
												{
													"text": "every 3 weeks (recurring)",
													"value": "every_3weeks"
												},
												{
													"text": "every month (recurring)",
													"value": "every_month"
												},
												{
													"text": "every 3 months (recurring)",
													"value": "every_3month"
												},
												{
													"text": "every 6 months (recurring)",
													"value": "every_6month"
												},
												
											],
											"selected_options": [
			                        			{
			                            			"text": value,
			                            			"value": value,
			                       			 	}
			                    			]
										}
										
									]
								}
					attachments_json12.append(attachment1)
				if resul['poll_time']=='':
					attachment3={"text":"*Date/Time* \n Date: *"+poll_date+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				else:
					attachment3={"text":"*Date/Time* \n Date: *"+poll_date+"* Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				if resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='yes' :
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger"}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='no' :
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='no' or resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='':
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='yes' or resul['allow_user_add_option']=='' and resul['max_vote_user']=='yes':						
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='' and resul['max_vote_user']=='':
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				if resul['send']=='':
					attachment5={"text":"*Poll Audience*  \n <#"+data['channel']['id']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				else:
					attachment5={"text":"*Poll Audience*  \n <#"+resul['send']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				attachment2={"text": " *SUBMIT / CANCEL* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll","style":"danger"}]}
				attachments_json12.append(attachment2)
				response_url=data['response_url']
				message= {'text':"<@"+data['user']['id']+"> used `/Event Manage bot`",'attachments':attachments_json12 ,'response_type': 'ephemeral','ts':ts,'replace_original': True}
				request_response = self.req_response(response_url , message)
				return Response(''),200

			else:
				poll_time=data['actions'][0]['selected_options'][0]['value']
				name=data['actions'][0]['name']
				poll_id=name.split("polltime_",1)[1]
				ts=data['message_ts']
				self.connection_start()
				sql = "UPDATE poll SET poll_time=%s WHERE poll_id=%s"
				self.cursor.execute(sql, (poll_time,poll_id))
				self.connection.commit()
				self.connection_start()
				self.cursor.execute("select poll_option ,poll_tittel,poll_reminder,poll_date,allow_user_add_option,max_vote_user from poll where poll_id='"+poll_id+"'")
				resul=self.cursor.fetchone()
				print(resul)
				date=resul['poll_date']
				print(date)
				old_option=resul['poll_option']
				qus=resul['poll_tittel']
				value=resul['poll_reminder']
				fetch_optin=json.loads(old_option)
				option_delete=[]
				i=1
				for option_data in fetch_optin:
					o={"option"+str(i):option_data['option']}
					option_delete.append(o)
					i=i+1
				print(option_delete)
				option1=option_delete[0]['option1']
				option2=option_delete[1]['option2']
				length=len(option_delete)
				if length > 2:
					option3=option_delete[2]['option3']
					print(option3)
				else:
					option3=None
				if length > 3:
					option4=option_delete[3]['option4'] 
					print(option4)
				else: 
					option4=None
				if length > 4:
					option5=option_delete[4]['option5'] 
					print(option5)
				else: 
					option5=None
				if length > 5:
					option6=option_delete[5]['option6'] 
					print(option6)
				else: 
					option6=None
				
				if length > 6:
					option7=option_delete[6]['option7'] 
					print(option7)
				else: 
					option7=None
				if length >7:
					option8=option_delete[7]['option8'] 
					print(option8)
				else: 
					option8=None

				if length==8:	
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								}							
							]
						}
					]
				else:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								},
								{
									"name": "addoption_"+poll_id,
									"text": "+ Add Option",
									"type": "button",
									"value": "Addoption",
								}									
							]
						}
					]

				if data['channel']['name']!='directmessage' and  data['channel']['name']!='privategroup':
					attachment1={
									"fallback":"THIS slack ",
									"callback_id": "polling_recurring",
									"color": "#3AA3E3",
									"attachment_type": "default",
									"actions": [
										{
											"name": "pollrimender_"+poll_id,
											
											"type": "select",
											"value": "selectpoll",
											"options": [
												{
													"text": "one time (recurring)",
													"value": "one_time"
												},
												{
													"text": "every time (recurring)",
													"value": "every time"
												},
												{
													"text": "every week (recurring)",
													"value": "every_week"
												},
												{
													"text": "every 2 weeks (recurring)",
													"value": "every_2weeks"
												},
												{
													"text": "every 3 weeks (recurring)",
													"value": "every_3weeks"
												},
												{
													"text": "every month (recurring)",
													"value": "every_month"
												},
												{
													"text": "every 3 months (recurring)",
													"value": "every_3month"
												},
												{
													"text": "every 6 months (recurring)",
													"value": "every_6month"
												},
												
											],
											"selected_options": [
			                        			{
			                            			"text": value,
			                            			"value": value,
			                       			 	}
			                    			]
										}
										
									]
								}
					attachments_json12.append(attachment1)
				if resul['poll_date']=='':
					attachment3={"text":"*Date/Time* \n Time: *"+poll_time+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				else:
					attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"* Time: *"+poll_time+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				if resul['allow_user_add_option']=='' and resul['max_vote_user']=='':
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='yes' :
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger"}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='no' or resul['allow_user_add_option']== ''and resul['max_vote_user']=='' :
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='no' or resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='':
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='yes' or resul['allow_user_add_option']=='' and resul['max_vote_user']=='yes':	
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				if resul['send']=='':
					attachment5={"text":"*Poll Audience*  \n <#"+data['channel']['id']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				else:
					attachment5={"text":"*Poll Audience*  \n <#"+resul['send']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				attachment2={"text": " *SUBMIT / CANCEL* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll","style":"danger",}]}
				attachments_json12.append(attachment2)
				response_url=data['response_url']
				message= {'text':"<@"+data['user']['id']+"> used `/Event Manage bot`",'attachments':attachments_json12 ,'response_type': 'ephemeral','ts':ts,'replace_original': True}
				request_response = self.req_response(response_url , message)
				return Response(''),200
		elif "poll_extra_option" == callback_id:
			name=data['actions'][0]['name']
			print(name)
			if "addingoptionusrer_" in name:
				button_value=data['actions'][0]['value']
				print("im adding")
				name=data['actions'][0]['name']
				poll_id=name.split("addingoptionusrer_",1)[1]
				ts=data['message_ts']
				self.connection_start()
				self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
				resul=self.cursor.fetchone()
				old_option=resul['poll_option']
				qus=resul['poll_tittel']
				fetch_optin=json.loads(old_option)
				option_delete=[]
				i=1
				for option_data in fetch_optin:
					o={"option"+str(i):option_data['option']}
					option_delete.append(o)
					i=i+1
				print(option_delete)
				option1=option_delete[0]['option1']
				option2=option_delete[1]['option2']
				length=len(option_delete)
				if length > 2:
					option3=option_delete[2]['option3']
					print(option3)
				else:
					option3=None
				if length > 3:
					option4=option_delete[3]['option4'] 
					print(option4)
				else: 
					option4=None
				if length > 4:
					option5=option_delete[4]['option5'] 
					print(option5)
				else: 
					option5=None
				if length > 5:
					option6=option_delete[5]['option6'] 
					print(option6)
				else: 
					option6=None
				
				if length > 6:
					option7=option_delete[6]['option7'] 
					print(option7)
				else: 
					option7=None
				if length >7:
					option8=option_delete[7]['option8'] 
					print(option8)
				else: 
					option8=None
				if length==8:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								},
																	
							]
						}
					]
				else:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								},
								{
									"name": "addoption_"+poll_id,
									"text": "+ Add Option",
									"type": "button",
									"value": "Addoption",
								}							
							]
						}
					]
				if data['channel']['name']!="directmessage" and data['channel']['name']!="privategroup":
					if resul['poll_reminder']!='':
						value=resul['poll_reminder']	
						attachment1={
										"fallback":"THIS slack ",
										"callback_id": "polling_recurring",
										"color": "#3AA3E3",
										"attachment_type": "default",
										"actions": [
											{
												"name": "pollrimender_"+poll_id,
												"type": "select",
												"value": "selectpoll",
												"options": [
													{
														"text": "one time (recurring)",
														"value": "one_time"
													},
													{
														"text": "every time (recurring)",
														"value": "every time"
													},
													{
														"text": "every week (recurring)",
														"value": "every_week"
													},
													{
														"text": "every 2 weeks (recurring)",
														"value": "every_2weeks"
													},
													{
														"text": "every 3 weeks (recurring)",
														"value": "every_3weeks"
													},
													{
														"text": "every month (recurring)",
														"value": "every_month"
													},
													{
														"text": "every 3 months (recurring)",
														"value": "every_3month"
													},
													{
														"text": "every 6 months (recurring)",
														"value": "every_6month"
													},
													
												],
												"selected_options": [
				                        			{
				                            			"text": value,
				                            			"value": value,
				                       			 	}
				                    			]
											}
											
										]
									}
						attachments_json12.append(attachment1)
					else:
						attachment1={
										"fallback":"THIS slack ",
										"callback_id": "polling_recurring",
										"color": "#3AA3E3",
										"attachment_type": "default",
										"actions": [
											{
												"name": "pollrimender_"+poll_id,
												
												"type": "select",
												"value": "selectpoll",
												"options": [
													{
														"text": "one time (recurring)",
														"value": "one_time"
													},
													{
														"text": "every time (recurring)",
														"value": "every time"
													},
													{
														"text": "every week (recurring)",
														"value": "every_week"
													},
													{
														"text": "every 2 weeks (recurring)",
														"value": "every_2weeks"
													},
													{
														"text": "every 3 weeks (recurring)",
														"value": "every_3weeks"
													},
													{
														"text": "every month (recurring)",
														"value": "every_month"
													},
													{
														"text": "every 3 months (recurring)",
														"value": "every_3month"
													},
													{
														"text": "every 6 months (recurring)",
														"value": "every_6month"
													},
													
												],
												"selected_options": [
				                        			{
				                            			"text": "one time (recurring)",
				                            			"value": "one_time",
				                       			 	}
				                    			]
											}
											
										]
									}
						attachments_json12.append(attachment1)

				if resul['poll_date']=='' and resul['poll_time']=='':
					attachment3={"text":"*Date/Time*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				elif resul['poll_date']!='' and resul['poll_time']=='': 
					attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				elif resul['poll_date']=='' and resul['poll_time']!='': 
					attachment3={"text":"*Date/Time* \n Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				elif resul['poll_date']!='' and resul['poll_time']!='': 
					attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"* Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)

				
				if "adding_option_user"==button_value and resul['max_vote_user']=="no" :
					sql = "UPDATE poll SET allow_user_add_option=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('yes',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger"}]}
					attachments_json12.append(attachment4)
				elif "accept_user"==button_value and resul['max_vote_user']=='no':
					sql = "UPDATE poll SET allow_user_add_option=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('no',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				elif "adding_option_user"==button_value and resul['max_vote_user']=='yes'   :
					sql = "UPDATE poll SET allow_user_add_option=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('yes',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger"}]}
					attachments_json12.append(attachment4)
				elif "accept_user"==button_value and resul['max_vote_user']=='yes' :
					sql = "UPDATE poll SET allow_user_add_option=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('no',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				if "accept_user"==button_value and resul['max_vote_user']=='':
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				
				if resul['send']=='':
					attachment5={"text":"*Poll Audience*  \n <#"+data['channel']['id']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				else:
					attachment5={"text":"*Poll Audience*  \n <#"+resul['send']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				attachment2={"text": " *SUBMIT / CANCEL* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll","style":"danger",}]}
				attachments_json12.append(attachment2)

				response_url=data['response_url']
				message= {'text':"<@"+data['user']['id']+"> used `/Event Manage bot`",'attachments':attachments_json12 ,'response_type': 'ephemeral','ts':ts,'replace_original': True}
				request_response = self.req_response(response_url , message)
				return Response(''),200
			if "vote_" in name:
				print(data)
				poll_id=name.split("vote_",1)[1]
				print(poll_id)
				button_value=data['actions'][0]['value']				
				self.connection_start()
				self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
				resul=self.cursor.fetchone()
				old_option=resul['poll_option']
				qus=resul['poll_tittel']
				fetch_optin=json.loads(old_option)
				option_delete=[]
				i=1
				for option_data in fetch_optin:
					o={"option"+str(i):option_data['option']}
					option_delete.append(o)
					i=i+1
				print(option_delete)
				option1=option_delete[0]['option1']
				option2=option_delete[1]['option2']
				length=len(option_delete)
				if length > 2:
					option3=option_delete[2]['option3']
					print(option3)
				else:
					option3=None
				if length > 3:
					option4=option_delete[3]['option4'] 
					print(option4)
				else: 
					option4=None
				if length > 4:
					option5=option_delete[4]['option5'] 
					print(option5)
				else: 
					option5=None
				if length > 5:
					option6=option_delete[5]['option6'] 
					print(option6)
				else: 
					option6=None
				
				if length > 6:
					option7=option_delete[6]['option7'] 
					print(option7)
				else: 
					option7=None
				if length >7:
					option8=option_delete[7]['option8'] 
					print(option8)
				else: 
					option8=None
				if length==8:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								},
																	
							]
						}
					]
				else:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								},
								{
									"name": "addoption_"+poll_id,
									"text": "+ Add Option",
									"type": "button",
									"value": "Addoption",
								}							
							]
						}
					]
				if data['channel']['name']!="directmessage" and data['channel']['name']!="privategroup":
					if resul['poll_reminder']!='':
						value=resul['poll_reminder']	
						attachment1={
										"fallback":"THIS slack ",
										"callback_id": "polling_recurring",
										"color": "#3AA3E3",
										"attachment_type": "default",
										"actions": [
											{
												"name": "pollrimender_"+poll_id,
												"type": "select",
												"value": "selectpoll",
												"options": [
													{
														"text": "one time (recurring)",
														"value": "one_time"
													},
													{
														"text": "every time (recurring)",
														"value": "every time"
													},
													{
														"text": "every week (recurring)",
														"value": "every_week"
													},
													{
														"text": "every 2 weeks (recurring)",
														"value": "every_2weeks"
													},
													{
														"text": "every 3 weeks (recurring)",
														"value": "every_3weeks"
													},
													{
														"text": "every month (recurring)",
														"value": "every_month"
													},
													{
														"text": "every 3 months (recurring)",
														"value": "every_3month"
													},
													{
														"text": "every 6 months (recurring)",
														"value": "every_6month"
													},
													
												],
												"selected_options": [
				                        			{
				                            			"text": value,
				                            			"value": value,
				                       			 	}
				                    			]
											}
											
										]
									}
						attachments_json12.append(attachment1)
					else:
						attachment1={
										"fallback":"THIS slack ",
										"callback_id": "polling_recurring",
										"color": "#3AA3E3",
										"attachment_type": "default",
										"actions": [
											{
												"name": "pollrimender_"+poll_id,
												
												"type": "select",
												"value": "selectpoll",
												"options": [
													{
														"text": "one time (recurring)",
														"value": "one_time"
													},
													{
														"text": "every time (recurring)",
														"value": "every time"
													},
													{
														"text": "every week (recurring)",
														"value": "every_week"
													},
													{
														"text": "every 2 weeks (recurring)",
														"value": "every_2weeks"
													},
													{
														"text": "every 3 weeks (recurring)",
														"value": "every_3weeks"
													},
													{
														"text": "every month (recurring)",
														"value": "every_month"
													},
													{
														"text": "every 3 months (recurring)",
														"value": "every_3month"
													},
													{
														"text": "every 6 months (recurring)",
														"value": "every_6month"
													},
													
												],
												"selected_options": [
				                        			{
				                            			"text": "one time (recurring)",
				                            			"value": "one_time",
				                       			 	}
				                    			]
											}
											
										]
									}
						attachments_json12.append(attachment1)
				if resul['poll_date']=='' and resul['poll_time']=='':
					attachment3={"text":"*Date/Time*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				elif resul['poll_date']!='' and resul['poll_time']=='': 
					attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				elif resul['poll_date']=='' and resul['poll_time']!='': 
					attachment3={"text":"*Date/Time* \n Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				elif resul['poll_date']!='' and resul['poll_time']!='': 
					attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"* Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				
				if resul['allow_user_add_option']=='yes' and button_value=="vote":
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('yes',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger"}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='no' and button_value=="more_vote":
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('no',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='yes' and button_value=="more_vote":
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('no',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='no' and button_value=="vote":	
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('yes',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				if resul['allow_user_add_option']=='' and button_value=="vote":
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('yes',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				
				elif resul['allow_user_add_option']==''and button_value=="more_vote":
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('no',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)

				if resul['send']=='':
					attachment5={"text":"*Poll Audience*  \n <#"+data['channel']['id']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				else:
					attachment5={"text":"*Poll Audience*  \n <#"+resul['send']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				attachment2={"text": " *SUBMIT / CANCEL* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll","style":"danger",}]}
				attachments_json12.append(attachment2)
				response_url=data['response_url']
				message= {'text':"<@"+data['user']['id']+"> used `/Event Manage bot`",'attachments':attachments_json12 ,'response_type': 'ephemeral','replace_original': True}
				request_response = self.req_response(response_url , message)
				return Response(''),200



		elif "polling_edit_option_" in callback_id:
			print(data)
			poll_id=callback_id.split("polling_edit_option_",1)[1]
			message_ts=callback_id.split(" ")
			print(message_ts)
			flag = False
			edit_op = []
			for key,value in data['submission'].items():
				if 'option_' in key:
					flag = True
					edit_op = key
			if flag:
				poll_option = edit_op.split("option_",1)[1]
				new_option=data['submission']['option_'+poll_option]
				self.connection_start()
				self.cursor.execute("select * from poll where poll_id='"+poll_id+"'")
				resul=self.cursor.fetchone()
				old_option=resul['poll_option']
				qus=resul['poll_tittel']
				print(resul)
				fetch_optin=json.loads(old_option)
				show_array=[]
				option_delete=[]
				i=1
				for option_data in fetch_optin:
					if poll_option==option_data['option']:
						db={"option":new_option}
						show_array.append(db)
						p={"option"+str(i):new_option}
						option_delete.append(p)
						i=i+1
					else:
						db={"option":option_data['option']}
						show_array.append(db)
						o={"option"+str(i):option_data['option']}
						option_delete.append(o)
						i=i+1
				print(option_delete)
				print(show_array)
				option1=option_delete[0]['option1']
				option2=option_delete[1]['option2']
				length=len(option_delete)
				if length > 2:
					option3=option_delete[2]['option3']
					print(option3)
				else:
					option3=None
				if length > 3:
					option4=option_delete[3]['option4'] 
					print(option4)
				else: 
					option4=None
				if length > 4:
					option5=option_delete[4]['option5'] 
					print(option5)
				else: 
					option5=None
				if length > 5:
					option6=option_delete[5]['option6'] 
					print(option6)
				else: 
					option6=None
				
				if length > 6:
					option7=option_delete[6]['option7'] 
					print(option7)
				else: 
					option7=None
				if length >7:
					option8=option_delete[7]['option8'] 
					print(option8)
				else: 
					option8=None
				if length==8:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]

						},
						{
							
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								}							
							]
						}
					]
				else:
					attachments_json12=[
						{
							"text": " *"+qus+"* ",
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option1,
									"type": "button",
									"value": option1,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option2,
									"type": "button",
									"value": option2,
								},
								{
									"name": "option_"+poll_id,
									"text": option3,
									"type": "button",
									"value": option3,
								},
								{
									"name": "option_"+poll_id,
									"text": option4,
									"type": "button",
									"value": option4,
								}							
							]
						},
						{
							"fallback":"THIS slack ",
							"callback_id": "polling_option",
							"color": "#3AA3E3",
							"attachment_type": "default",
							"actions": [
								{
									"name": "option_"+poll_id,
									"text":option5,
									"type": "button",
									"value": option5,

								}, 
								{
									"name": "option_"+poll_id,
									"text": option6,
									"type": "button",
									"value": option6,
								},
								{
									"name": "option_"+poll_id,
									"text": option7,
									"type": "button",
									"value": option7,
								},
								{
									"name": "option_"+poll_id,
									"text": option8,
									"type": "button",
									"value": option8,
								},	
								{
									"name": "addoption_"+poll_id,
									"text": "+ Add Option",
									"type": "button",
									"value": "Addoption",
								}								
							]
						}
					]
				if data['channel']['name']!="directmessage" and data['channel']['name']!="privategroup":
					if resul['poll_reminder']!='':
						value=resul['poll_reminder']	
						attachment1={
										"fallback":"THIS slack ",
										"callback_id": "polling_recurring",
										"color": "#3AA3E3",
										"attachment_type": "default",
										"actions": [
											{
												"name": "pollrimender_"+poll_id,
												"type": "select",
												"value": "selectpoll",
												"options": [
													{
														"text": "one time (recurring)",
														"value": "one_time"
													},
													{
														"text": "every time (recurring)",
														"value": "every time"
													},
													{
														"text": "every week (recurring)",
														"value": "every_week"
													},
													{
														"text": "every 2 weeks (recurring)",
														"value": "every_2weeks"
													},
													{
														"text": "every 3 weeks (recurring)",
														"value": "every_3weeks"
													},
													{
														"text": "every month (recurring)",
														"value": "every_month"
													},
													{
														"text": "every 3 months (recurring)",
														"value": "every_3month"
													},
													{
														"text": "every 6 months (recurring)",
														"value": "every_6month"
													},
													
												],
												"selected_options": [
				                        			{
				                            			"text": value,
				                            			"value": value,
				                       			 	}
				                    			]
											}
											
										]
									}
						attachments_json12.append(attachment1)
					else:
						attachment1={
										"fallback":"THIS slack ",
										"callback_id": "polling_recurring",
										"color": "#3AA3E3",
										"attachment_type": "default",
										"actions": [
											{
												"name": "pollrimender_"+poll_id,
												
												"type": "select",
												"value": "selectpoll",
												"options": [
													{
														"text": "one time (recurring)",
														"value": "one_time"
													},
													{
														"text": "every time (recurring)",
														"value": "every time"
													},
													{
														"text": "every week (recurring)",
														"value": "every_week"
													},
													{
														"text": "every 2 weeks (recurring)",
														"value": "every_2weeks"
													},
													{
														"text": "every 3 weeks (recurring)",
														"value": "every_3weeks"
													},
													{
														"text": "every month (recurring)",
														"value": "every_month"
													},
													{
														"text": "every 3 months (recurring)",
														"value": "every_3month"
													},
													{
														"text": "every 6 months (recurring)",
														"value": "every_6month"
													},
													
												],
												"selected_options": [
				                        			{
				                            			"text": "one time (recurring)",
				                            			"value": "one_time",
				                       			 	}
				                    			]
											}
											
										]
									}
						attachments_json12.append(attachment1)
				if resul['poll_date']=='' and resul['poll_time']!='':
					attachment3={"text":"*Date/Time* \n Time: *"+poll_time+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				elif resul['poll_date']!='' and resul['poll_time']!='':
					attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"* Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				elif resul['poll_date']!='' and resul['poll_time']!='':
					attachment3={"text":"*Date/Time* \n Date: *"+resul['poll_date']+"* Time: *"+resul['poll_time']+"*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)
				elif resul['poll_date']=='' and resul['poll_time']=='':
					attachment3={"text":"*Date/Time*","fallback":"THIS ","callback_id": "poll_date_time","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "polldate_"+poll_id,"text": "Select a Date","type": "select","data_source": "external","min_query_length": 0,},{"name": "polltime_"+poll_id,"text": "Select a Time","type": "select","data_source": "external","min_query_length": 0,}]}
					attachments_json12.append(attachment3)

				if resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='yes' :
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('yes',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger"}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='no' or resul['allow_user_add_option']=='' and resul['max_vote_user']=='' :
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('no',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='no' or resul['allow_user_add_option']=='yes' and resul['max_vote_user']=='':
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('no',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": ":thumbsup_all:One Vote Max","type": "button","value":"vote","style": "primary",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"accept_user","style":"danger",}]}
					attachments_json12.append(attachment4)
				elif resul['allow_user_add_option']=='no' and resul['max_vote_user']=='yes' or resul['allow_user_add_option']=='' and resul['max_vote_user']=='yes':	
					sql = "UPDATE poll SET max_vote_user=%s WHERE poll_id=%s"
					self.cursor.execute(sql, ('yes',poll_id))
					self.connection.commit()
					attachment4={"text":"*POLL OPTIONS*","fallback":"THIS ","callback_id": "poll_extra_option","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "vote_"+poll_id,"text": "One Vote Max","type": "button","value":"more_vote",},{"name": "hideresult_"+poll_id,"text": ":ballot_box_with_ballot:Hide Result","type": "button","value":"hideresult",},{"name": "anonymous_"+poll_id,"text": "Anonymous","type": "button","value":"anonymous",},{"name": "commentprivate_"+poll_id,"text": ":white_check_mark:Private Comment","type": "button","value":"private_comment","style":"primary",},{"name": "addingoptionusrer_"+poll_id,"text": "Allow Adding Option","type": "button","value":"adding_option_user",}]}
					attachments_json12.append(attachment4)
				if resul['send']=='':
					attachment5={"text":"*Poll Audience*  \n <#"+data['channel']['id']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				else:
					attachment5={"text":"*Poll Audience*  \n <#"+resul['send']+">" ,"fallback":"THIS ","callback_id": "poll_audience","color": "#3AA3E3","attachment_type": "default","actions":[{"name":"pollchannel_"+poll_id,"text": "Select Audience","type": "select","data_source": "channels"}]}
					attachments_json12.append(attachment5)
				attachment2={"text": " *SUBMIT* ","fallback":"THIS slack ","callback_id": "polling_submit","color": "#3AA3E3","attachment_type": "default","actions": [{"name": "pollsubmit_"+poll_id,"text":"Submit","type": "button","value": "submit_poll",},{"name": "polladvanceoptions_"+poll_id,"text":"Advanced Option","type": "button","value": "poll_advance_option",},{"name": "cancelpoll_"+poll_id,"text":"Cancel","type": "button","value": "cancel_poll",}]}
				attachments_json12.append(attachment2)

				db_option=json.dumps(show_array)
				sql = "UPDATE poll SET poll_option=%s WHERE poll_id=%s"
				self.cursor.execute(sql, (db_option,poll_id))
				self.connection.commit()
				response_url=data['response_url']
				message= {'text':"<@"+data['user']['id']+"> used `/Event Manage bot`",'attachments':attachments_json12 ,'response_type': 'ephemeral','replace_original': True}
				request_response = self.req_response(response_url , message)
				return Response(''),200

	def external_data(self):
		response_data = request.form.get('payload')
		data= json.loads(response_data)   
		print("hello date")     
		call=data['callback_id']
		print(call)
		if data['callback_id']=='new_event_create' and  'external_date_' in data['name'] or data['callback_id']=='new_event_create' and  'edit_date_' in data['name'] or data['callback_id']=="poll_date_time" and "polldate_" in data['name']:
			print("come")
			input_month = ''
			input_day = ''
			input_date = ''
			output_dates = []
			if len(data['value']) > 2:
				if data['value'].lower().startswith("jan"):
					input_month = 'Jan'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("feb"):
					input_month = 'Feb'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("mar"):
					input_month = 'Mar'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("apr"):
					input_month = 'Apr'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("may"):
					input_month = 'May'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("jun"):
					input_month = 'Jun'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("jul"):
					input_month = 'Sun'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("aug"):
					input_month = 'Aug'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("sep"):
					input_month = 'Sep'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("oct"):
					input_month = 'Oct'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("nov"):
					input_month = 'Nov'
					input_date = re.findall('\d+', data['value'])
				elif data['value'].lower().startswith("dec"):
					input_month = 'Dec'
					input_date = re.findall('\d+', data['value'])
				start_dt = datetime.now()
				end_dt = start_dt + timedelta(days=365)

				if len(input_date) != 0:
					if len(str(input_date[0])) == 1:
						input_date = input_date[0].zfill(2)
					else:
						input_date = input_date[0]

				if input_month is not None:
					if len(input_date) != 0:
						for dt in self.daterange(start_dt, end_dt):
							if dt.strftime("%b") == input_month and dt.strftime("%d") == input_date:
								output_dates.append({"text":dt.strftime("%b %d") ,"value": dt.strftime("%d-%m")})
					elif len(input_date) == 0:
						for dt in self.daterange(start_dt, end_dt):
							if dt.strftime("%b") == input_month:
								output_dates.append({"text":dt.strftime("%b %d") ,"value": dt.strftime("%d-%m")})

				if input_day is not None:
					if len(input_date) != 0:
						for dt in self.daterange(start_dt, end_dt):
							if dt.strftime("%a") == input_day and dt.strftime("%d") == input_date:
								output_dates.append({"text":dt.strftime("%b %d") ,"value": dt.strftime("%d-%m")})
					elif len(input_date) == 0:
						for dt in self.daterange(start_dt, end_dt):
							if dt.strftime("%a") == input_day:
								output_dates.append({"text":dt.strftime("%b %d") ,"value": dt.strftime("%d-%m")})
				DateOptions = {"options": output_dates}
				return Response(json.dumps(DateOptions), headers={'Content-Type': 'application/json','X-Slack-Retry-Num': 2}),200
			else:
				start_dt = datetime.now()
				end_dt = start_dt + timedelta(days=30)
				for dt in self.daterange(start_dt, end_dt):
					output_dates.append({"text":dt.strftime("%b %d") ,"value": dt.strftime("%d-%m")})
					DateOptions = {"options": output_dates}
				return Response(json.dumps(DateOptions), headers={'Content-Type': 'application/json','X-Slack-Retry-Num': 2}),200
	   
		elif data['callback_id']=='new_event_create' and 'external_time_' in data['name'] or data['callback_id']=='new_event_create' and 'edit_time_' in data['name'] or data['callback_id']=="poll_date_time" and "polltime_" in data['name']:
			user = data['user']['id']
			response = slack_client.api_call('users.info', user=user)
			if response['ok'] == True:
				tz_offset = response['user']['tz_offset']
				if len(data['value']) > 1:
					contains_s = data['value'].strip()
					if contains_s:
						time_arr = []
						time_re = re.compile(r'^(0[0-9]|1[0-12]):[0-5][0-9] ?((a|p)m|(A|P)M)$')
						chosen_t = bool(time_re.match(contains_s))
						if chosen_t:
							if contains_s[5] == " ":
								text = contains_s.upper()
								time_arr.append({"text":text ,"value": text})
							else:
								time_am = contains_s[5:].upper()
								text = contains_s[0:5]+" "+time_am
								time_arr.append({"text":text ,"value": text})
							TimeOptions = {"options": time_arr}
							return Response(json.dumps(TimeOptions), headers={'Content-Type': 'application/json','X-Slack-Retry-Num': 2}),200 
						else:
							chose_time= str(data['value'].strip())
							time_arr = []
							time_re = re.compile(r'^(0[0-9]|1[012])')
							chosen_time = bool(time_re.match(contains_s))
							
							if chosen_time:
								a=0
								for i in range(0,11):
									total=a
									total=total+5
									a=total
									time_arr.append({"text":str(chose_time+":"+str(a)+" "+"AM") ,"value": str(chose_time+":"+str(a)+" "+"AM")})
								TimeOptions = {"options": time_arr}
								p=0
								for i in range(0,11):
									total=p
									total=total+5
									p=total
									time_arr.append({"text":str(chose_time+":"+str(p)+" "+"PM") ,"value": str(chose_time+":"+str(p)+" "+"PM")})
								TimeOptions = {"options": time_arr}
							return Response(json.dumps(TimeOptions), headers={'Content-Type': 'application/json','X-Slack-Retry-Num': 2}),200
				else:
					current_utc = datetime.utcnow()
					t=current_utc.timetuple()
					received_t = time.mktime(t)+tz_offset
					current_time = datetime.fromtimestamp(received_t)
					current_minute = current_time.minute
					upper_min = current_minute                   
					while ( upper_min % 1 ) != 0:
						upper_min+=1                    
					current_time = current_time + timedelta(minutes = (upper_min - current_minute))
					limit = 0
					time_arr = []
					while limit < 60:
						limit+=1
						text = current_time.strftime("%I:%M %p")
						time_arr.append({"text":text ,"value": text})
						current_time = current_time + timedelta(minutes = 10)
					TimeOptions = {"options": time_arr}
			  
					return Response(json.dumps(TimeOptions), headers={'Content-Type': 'application/json','X-Slack-Retry-Num': 2}),200
		return Response('',headers={'X-Slack-Retry-Num': 2}),200

	def daterange(self,date1,date2):
		for n in range(int ((date2 - date1).days)+1):
			yield date1 + timedelta(n)
	def event_auto(self):
		data =json.loads(request.get_data(as_text=True))
		# challenge=data['challenge']
		# return Response(challenge),200
		self.connection_start()
		self.cursor.execute("select * from create_full_event")
		result1=self.cursor.fetchall()
		data_label=[]
		for custom_label in result1:
			data_row = {
				"text": custom_label['label'],
				"value": custom_label['id']
			}
			data_label.append(data_row)
		try:
			channel=data['event']['channel']
			message=data['event']['text']
			event_id=data['event_id']
			team_id=data['team_id']
			user_id=data['event']['user']
			text=message.lower()
			if text=="help":
				attachments_json12 = [
					{
						"text": " *Features*\n Select Your Event ",
						"fallback":"THIS folt by slack ",
						"callback_id": "new_event_create",
						"color": "#3AA3E3",
						"attachment_type": "default",
						"actions": [
							{
								"name": "birthday_"+event_id,
								"text": ":cake:BIRTHDAY",
								"type": "button",
								"value": "birthday",
							}, 
							{
								"name": "anniversary_"+event_id,
								"text": ":tada:anniversary",
								"type": "button",
								"value": "edit",
							},
							{
								"name": "assign_"+event_id,
								"text": "Create Event",
								"type": "button",
								"value": "new_event",
							},
							{
								"name": "setting_"+event_id,
								"text": ":gear:Setting",
								"type": "button",
								"value": "setting",
							},
							{
								"name": "select",
								"text": "Show Event",
								"type": "select",
								"options": data_label    
								
							}

						]
					   
					}
				]
				r=slack_client.api_call("chat.postMessage",channel=channel,attachments= attachments_json12,text="thank u for Subscribe to Bot.",as_user=True)
				self.connection_start()
				ts=r['ts']
				sql = "INSERT INTO  create_event (`event_id`, `ts`, `team_id` , `user_id`)VALUES(%s, %s, %s, %s)"
				self.cursor.execute(sql, (event_id,ts,team_id,user_id))
				self.connection.commit()
			return Response('',headers={'X-Slack-Retry-Num':1}),200
		except Exception as e:
			return Response("",headers={'X-Slack-Retry-Num': 2}),200

	def req_response(self,response_url,message):
		response = requests.post(response_url, data=json.dumps(message), headers={'Content-Type': 'application/json'})
		print("response")
		print(response)
		return response

	def check_list(self):
		data=request.form
		channel_id=data['channel_id']
		user_id=data['user_id']
		self.connection_start()	
		if data['text']=="":
			self.cursor.execute("select list from to_do_list where list_user_id='"+user_id+"' and channel_id='"+channel_id+"'")
			fetch_list=self.cursor.fetchall()
			if fetch_list==():
					response_url=data['response_url']
					message= {'text':"One moment...",'response_type': 'ephemeral', 'replace_original': True}
					request_response = self.req_response(response_url , message)
					message= {'text':"NO USER TRY AGAIN OR NO LIST",'response_type': 'ephemeral', 'replace_original': True}
					request_response = self.req_response(response_url , message)
					return Response(''),200
			else:	
				response_url=data['response_url']
				message= {'text':"One moment...",'response_type': 'ephemeral', 'replace_original': True}
				request_response = self.req_response(response_url , message)
				self.cursor.execute("select list from to_do_list where list_user_id='"+user_id+"' and channel_id='"+channel_id+"'")
				fetch_list=self.cursor.fetchone()
				t=fetch_list['list']
				fetch_list1=json.loads(t)
				i=0
				text=str("")
				last_list=[]
				for user_list in fetch_list1:
					num=1
					i=num+i
					num=i
					num=str(num)
					text = text + (num +") "+ user_list['menu']+"\n")
				message= {'text':text,'response_type': 'in_channel', 'replace_original': True}
				request_response = self.req_response(response_url , message)
				return Response(''),200
		else:
			if data['text']=="clear":
				response_url=data['response_url']
				message= {'text':"One moment...",'response_type': 'ephemeral', 'replace_original': True}
				request_response = self.req_response(response_url , message)
				self.cursor.execute("DELETE  FROM `to_do_list` WHERE  list_user_id='"+user_id+"' and channel_id='"+channel_id+"'")
				self.connection.commit()
				message= {'text':"CLEAR LIST",'response_type': 'in_channel', 'replace_original': True}
				request_response = self.req_response(response_url , message)
				return Response(''),200

			else:
				text=data['text']
				print(text)
				dif=text.split(" ",1)
				pre=dif[0]
				if pre=="delete":
					post=dif[1]
					self.cursor.execute("select list from to_do_list where list_user_id='"+user_id+"' and channel_id='"+channel_id+"'")
					fetch_list=self.cursor.fetchone()
					t=fetch_list['list']
					fetch_list1=json.loads(t)
					arr_delete=[]
					j=1
					for list_data in fetch_list1:
						for key,value in list_data.items():
							if post!=str(j):
								no_list={j:value}
								arr_delete.append(no_list)		
							j=j+1
					response_url=data['response_url']
					message= {'text':"DELETE ITEM",'response_type': 'ephemeral', 'replace_original': True}
					request_response = self.req_response(response_url , message)
					old_arr=[]
					for old_list in arr_delete:
						for key,value in old_list.items():
							menu_list={'menu':value}
							old_arr.append(menu_list)
					arr_list=json.dumps(old_arr)
					sql = "UPDATE to_do_list SET list=%s WHERE list_user_id=%s and channel_id=%s"
					self.cursor.execute(sql, (arr_list, user_id, channel_id))
					self.connection.commit()
					return Response(''),200
				elif pre=="add":
					post=dif[1]
					print(post)
					response_url=data['response_url']
					message= {'text':"One moment...",'response_type': 'ephemeral', 'replace_original': True}
					request_response = self.req_response(response_url , message)
					self.cursor.execute("select * from to_do_list where list_user_id='"+user_id+"' and channel_id='"+channel_id+"'")
					ds=self.cursor.fetchall()
					if ds!=():	
						text1="<@"+data['user_id']+"> added `"+post+"` to the list"
						message= {'text':text1,'response_type': 'in_channel', 'replace_original': True}
						request_response = self.req_response(response_url , message)
						arr_list=[]
						self.cursor.execute("select list from to_do_list where list_user_id='"+user_id+"' and channel_id='"+channel_id+"'")
						fetch_list=self.cursor.fetchall()
						arr_list=(json.loads(fetch_list[0]['list']))
						to_do={"menu":post}
						arr_list.append(to_do)
						user_list=json.dumps(arr_list)
						sql = "UPDATE to_do_list SET list=%s WHERE list_user_id=%s and channel_id=%s"
						self.cursor.execute(sql, (user_list, user_id, channel_id))
						self.connection.commit()
						return Response(''),200
					else:
						arr_list=[]
						text1="<@"+data['user_id']+"> added `"+post+"` to the list"
						message= {'text':text1,'response_type': 'in_channel', 'replace_original': True}
						request_response = self.req_response(response_url , message)
						to_do={"menu":post}
						arr_list.append(to_do)
						user_list=json.dumps(arr_list)	
						sql = "INSERT INTO  to_do_list (`list_user_id`, `channel_id`, `list`)VALUES(%s ,%s,%s)"
						self.cursor.execute(sql, (user_id,channel_id,user_list))
						self.connection.commit()
						return Response(''),200
					
				elif data['text']!='':
					response_url=data['response_url']
					message= {'text':"One moment...",'response_type': 'ephemeral', 'replace_original': True}
					request_response = self.req_response(response_url , message)
					self.cursor.execute("select * from to_do_list where list_user_id='"+user_id+"' and channel_id='"+channel_id+"'")
					ds=self.cursor.fetchall()
					if ds!=():	
						text1="<@"+data['user_id']+"> added `"+text+"` to the list"
						message= {'text':text1,'response_type': 'in_channel', 'replace_original': True}
						request_response = self.req_response(response_url , message)
						arr_list=[]
						self.cursor.execute("select list from to_do_list where list_user_id='"+user_id+"' and channel_id='"+channel_id+"'")
						fetch_list=self.cursor.fetchall()
						arr_list=(json.loads(fetch_list[0]['list']))
						to_do={"menu":text}
						arr_list.append(to_do)
						user_list=json.dumps(arr_list)
						sql = "UPDATE to_do_list SET list=%s WHERE list_user_id=%s and channel_id=%s"
						self.cursor.execute(sql, (user_list, user_id, channel_id))
						self.connection.commit()
						return Response(''),200
					else:
						arr_list=[]
						text1="<@"+data['user_id']+"> added `"+text+"` to the list"
						message= {'text':text1,'response_type': 'in_channel', 'replace_original': True}
						request_response = self.req_response(response_url , message)
						to_do={"menu":text}
						arr_list.append(to_do)
						user_list=json.dumps(arr_list)	
						sql = "INSERT INTO  to_do_list (`list_user_id`, `channel_id`, `list`)VALUES(%s ,%s,%s)"
						self.cursor.execute(sql, (user_id,channel_id,user_list))
						self.connection.commit()
						return Response(''),200
	
	def manage_survey(self):
		data=request.form
		print(data)
		data=request.form
		channel_id=data['channel_id']
		poll_user_id=data['user_id']
		if data['text']!='':
			slack_client.api_call('dialog.open', trigger_id=data['trigger_id'],channel=data['channel_id'],
						dialog={
									
									"trigger_id":data['trigger_id'],
									"callback_id": "polling_question",
									"title": "Request a Ride",
									"submit_label": "Request",
									"elements": [
										{
											"type": "text",
											"label": "Question:",
											"value":data['text'],
											"name": "question1_"+poll_user_id,
											"placeholder": "Enter question"

										},
										{
											"type": "text",
											"label": "Option 1:",
											"name":"option1",
											"placeholder": "Enter 1st option"
										},
										{
											"type": "text",
											"label": "Option 2:",
											"name":"option2",
											"placeholder": "Enter 2st option"
										},
										{
											"type": "text",
											"label": "Option 3:",
											"name":"option3",
											"placeholder": "Enter 3st option",
											"optional":True
										},
										{
											"type": "text",
											"label": "Option 4:",
											"name":"option4",
											"placeholder": "Enter 4st option",
											"optional":True
										}
									 ]
								})
			return Response(''),200
		else:
			slack_client.api_call('dialog.open', trigger_id=data['trigger_id'],channel=data['channel_id'],
						dialog={
									"text":data['text'],
									"trigger_id":data['trigger_id'],
									"callback_id": "polling_question",
									"title": "Your POll",
									"submit_label": "Request",
									"elements": [
										{
											"type": "text",
											"label": "Question:",
											"value":data['text'],
											"name": "question1_"+poll_user_id,
											"placeholder": "Enter your question",
										
										},
										{
											"type": "text",
											"label": "Option 1:",
											"name":"option1",
											"placeholder": "Enter 1st option",
											
										},
										{
											"type": "text",
											"label": "Option 2:",
											"name":"option2",
											"placeholder": "Enter 2st option",
											
										},
										{
											"type": "text",
											"label": "Option 3:",
											"name":"option3",
											"placeholder": "Enter 3st option",
											"optional":True
										},
										{
											"type": "text",
											"label": "Option 4:",
											"name":"option4",
											"placeholder": "Enter 4st option",
											"optional":True
										}
									 ]
								})
			return Response(''),200


