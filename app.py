"""
This software is provided "as is," without warranty of any kind, express or implied,
including but not limited to the warranties of merchantability, fitness for a particular
purpose and noninfringement. In no event shall the authors or copyright holders be
liable for any claim, damages or other liability, whether in an action of contract,
tort or otherwise, arising from, out of or in connection with the software or the use
or other dealings in the software.

Limitation of Liability: In no event shall the authors or copyright holders be liable for any indirect, incidental, special, or consequential damages.

External Libraries: If this code relies on external libraries, please consult the disclaimers provided by those libraries.

License: MIT License.

Intended Use: This code is intended for educational purposes.
"""

import os
import re
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

# Initialize your app with your bot token
app = App(token=SLACK_BOT_TOKEN)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mock data for approvals with initial state as "pending"
approvals = [
    {
        "id": "1",
        "title": "May Expenses",
        "requestor": "U02PGRD77E1",  # Use Slack user IDs
        "amount": "AUD $1,000",
        "total": "AUD $1,000",
        "date": "2024-05-27",
        "employee": "U02PGRD77E1",  # Use Slack user IDs
        "status": "pending",
        "file_url": "",
        "custom_file_name": "",  # Add custom file name
        "image_url": "https://example.com/image.png",  # Add image URL
        "home_ts": "",
        "type": "expense"
    }
    # Add more mock approvals here
]

# Function to generate a unique ID for new approvals
def generate_approval_id():
    return str(len(approvals) + 1)

# Function to fetch user information from Slack
def get_user_info(client, user_id):
    try:
        response = client.users_info(user=user_id)
        if response["ok"]:
            return response["user"]["name"]
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
    return user_id  # Fallback to user ID if fetching fails

# Home Tab view
def home_tab_view(client, approvals, filter_status):
    blocks = [
        {
            "type": "actions",
            "block_id": "filter_section",
            "elements": [
                {
                    "type": "static_select",
                    "action_id": "filter_approvals",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "All Approvals"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "All approvals"
                            },
                            "value": "all"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Approved"
                            },
                            "value": "approved"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Pending"
                            },
                            "value": "pending"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Rejected"
                            },
                            "value": "rejected"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Recalled"
                            },
                            "value": "recalled"
                        }
                    ]
                },
                {
                    "type": "overflow",
                    "action_id": "actions_overflow",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "New Approval"
                            },
                            "value": "new_approval"
                        }
                    ]
                }
            ]
        },
        {
            "type": "divider"
        }
    ]

    filtered_approvals = [a for a in approvals if a.get("status") == filter_status or filter_status == "all"]

    if not filtered_approvals:
        no_approvals_message = "*You have no approval requests right now.*"
        if filter_status == "approved":
            no_approvals_message = "*You have no _approved_ approval requests right now.*"
        elif filter_status == "pending":
            no_approvals_message = "*You have no _pending_ approval requests right now.*"
        elif filter_status == "rejected":
            no_approvals_message = "*You have no _rejected_ approval requests right now.*"
        elif filter_status == "recalled":
            no_approvals_message = "*You have no _recalled_ approval requests right now.*"

        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": no_approvals_message
                }
            }
        )
    else:
        for approval in filtered_approvals:
            requestor_name = f"<@{approval['requestor']}>"
            employee_name = f"<@{approval['employee']}>"

            if approval["type"] == "expense":
                section_block = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{requestor_name} requests your approval for an Expense:"
                    }
                }
            elif approval["type"] == "time_off":
                section_block = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{employee_name} requests your approval for Time Off:"
                    }
                }
            blocks.append(section_block)

            if approval["type"] == "expense":
                section_block = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Expense | {approval['title']}*\n\n*Requestor:* {requestor_name}\n*Requested Amount:* {approval['amount']}\n*Report Total:* {approval['total']}\n*Report Date:* {approval['date']}\n*Employee Name:* {employee_name}"
                    }
                }
                if approval.get("image_url"):
                    section_block["accessory"] = {
                        "type": "image",
                        "image_url": approval["image_url"],
                        "alt_text": "Approval Image"
                    }
                blocks.append(section_block)
                if approval.get("file_url"):
                    file_display_name = approval["custom_file_name"] or approval["file_url"].split('/')[-1]
                    blocks.append(
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Attachments:* <{approval['file_url']}|{file_display_name}>"
                            }
                        }
                    )
            elif approval["type"] == "time_off":
                section_block = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Time Off Request*\n\n*Employee Name:* {employee_name}\n*Requested On:* {approval['request_date']}\n*Request Type:* {approval['request_type']}\n*Time Requested:* {approval['time_requested']}\n*Summary:* {approval['summary']} days\n*Notes:* {approval['notes']}"
                    }
                }
                if approval.get("image_url"):
                    section_block["accessory"] = {
                        "type": "image",
                        "image_url": approval["image_url"],
                        "alt_text": "Approval Image"
                    }
                blocks.append(section_block)
            
            if approval["status"] == "pending":
                blocks.append(
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "style": "primary",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Approve",
                                    "emoji": True
                                },
                                "value": approval['id'],
                                "action_id": "approve"
                            },
                            {
                                "type": "button",
                                "style": "danger",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Reject",
                                    "emoji": True
                                },
                                "value": approval['id'],
                                "action_id": "reject"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Details",
                                    "emoji": True
                                },
                                "value": approval['id'],
                                "action_id": "view_details"
                            },
                            {
                                "type": "overflow",
                                "action_id": "overflow",
                                "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Revert to Pending"
                                        },
                                        "value": f"revert-{approval['id']}"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Edit"
                                        },
                                        "value": f"edit-{approval['id']}"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Delete"
                                        },
                                        "value": f"delete-{approval['id']}"
                                    }
                                ]
                            }
                        ]
                    }
                )
            else:
                status_text = approval["status"].capitalize()
                if approval["status"] == "approved":
                    status_text = "Approved ✅"
                elif approval["status"] == "rejected":
                    status_text = "Rejected ❌"
                
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Status:* {status_text} on {approval['timestamp']}"
                        }
                    }
                )
                if approval["status"] == "rejected" and approval.get("comments"):
                    blocks.append(
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Comments:* {approval['comments']}"
                            }
                        }
                    )
                blocks.append(
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "overflow",
                                "action_id": "overflow",
                                "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Revert to Pending"
                                        },
                                        "value": f"revert-{approval['id']}"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Edit"
                                        },
                                        "value": f"edit-{approval['id']}"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Delete"
                                        },
                                        "value": f"delete-{approval['id']}"
                                    }
                                ]
                            }
                        ]
                    }
                )
            blocks.append(
                {
                    "type": "divider"
                }
            )
    return {"type": "home", "blocks": blocks}

# App Home Opened Event
@app.event("app_home_opened")
def update_home_tab(client, event):
    user_id = event["user"]
    logger.debug(f"App Home opened by user: {user_id}")
    view = home_tab_view(client, approvals, "all")
    try:
        response = client.views_publish(user_id=user_id, view=view)
        logger.debug(f"Home tab updated successfully: {response['ts']}")
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")

# Update approval status
def update_approval_status(client, approval_id, status, user_id):
    for approval in approvals:
        if approval["id"] == approval_id:
            approval["status"] = status
            approval["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
            break
    update_home_tab(client, {"user": user_id})
    
    # Send DM notification
    send_dm_notification(client, approval, status)

def send_dm_notification(client, approval, status):
    status_text = "Approved ✅" if status == "approved" else "Rejected ❌"
    requestor_name = f"<@{approval['requestor']}>"
    employee_name = f"<@{approval['employee']}>"

    if approval["type"] == "time_off":
        message_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Time Off Request*\n\n*Employee Name:* {employee_name}\n*Requested On:* {approval['request_date']}\n*Request Type:* {approval['request_type']}\n*Time Requested:* {approval['time_requested']}\n*Summary:* {approval['summary']} days\n*Notes:* {approval['notes']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Status:* {status_text} on {approval['timestamp']}"
                }
            }
        ]
    else:
        message_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{approval['type'].capitalize()} | {approval['title']}*\n\n*Requestor:* {requestor_name}\n*Requested Amount:* {approval.get('amount', '')}\n*Report Total:* {approval.get('total', '')}\n*Report Date:* {approval.get('date', '')}\n*Employee Name:* {employee_name}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Status:* {status_text} on {approval['timestamp']}"
                }
            }
        ]

        if approval.get("file_url"):
            file_display_name = approval["custom_file_name"] or approval["file_url"].split('/')[-1]
            message_blocks.insert(1, 
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Attachments:* <{approval['file_url']}|{file_display_name}>"
                    }
                }
            )

    if approval.get("image_url"):
        message_blocks[0]["accessory"] = {
            "type": "image",
            "image_url": approval["image_url"],
            "alt_text": "Approval Image"
        }

    if status == "rejected" and approval.get("comments"):
        message_blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Comments:* {approval['comments']}"
                }
            }
        )

    try:
        client.chat_postMessage(
            channel=approval['employee'],
            blocks=message_blocks,
            text=f"Your {approval['type']} request has been {status_text.lower()}."
        )
    except Exception as e:
        logger.error(f"Error sending DM notification: {e}")

# Button Actions
@app.action("approve")
def handle_approve(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    approval_id = body["actions"][0]["value"]
    logger.debug(f"Approval {approval_id} approved by user: {user_id}")
    update_approval_status(client, approval_id, "approved", user_id)

@app.action("reject")
def handle_reject(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    approval_id = body["actions"][0]["value"]
    logger.debug(f"Approval {approval_id} rejected by user: {user_id}")

    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": f"reject_modal-{approval_id}",
            "title": {
                "type": "plain_text",
                "text": "Add Comments"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "comments_input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "comments",
                        "multiline": True
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Comments"
                    }
                }
            ],
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            }
        }
    )

@app.view(re.compile(r"reject_modal-\d+"))
def handle_reject_submission(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    state_values = body["view"]["state"]["values"]
    approval_id = body["view"]["callback_id"].split('-')[-1]
    comments = state_values["comments_input"]["comments"]["value"]
    logger.debug(f"Approval {approval_id} rejection comments: {comments}")

    for approval in approvals:
        if approval["id"] == approval_id:
            approval["status"] = "rejected"
            approval["comments"] = comments
            approval["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
            break
    update_approval_status(client, approval_id, "rejected", user_id)

@app.action("view_details")
def handle_view_details(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    approval_id = body["actions"][0]["value"]
    logger.debug(f"View details for approval {approval_id} requested by user: {user_id}")
    
    for approval in approvals:
        if approval["id"] == approval_id:
            detail_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{approval['type'].capitalize()} | {approval['title']}*\n\n*Requestor:* <@{approval['requestor']}>\n*Requested Amount:* {approval.get('amount', '')}\n*Report Total:* {approval.get('total', '')}\n*Report Date:* {approval.get('date', '')}\n*Employee Name:* <@{approval['employee']}>"
                    }
                }
            ]
            
            if approval["type"] == "expense" and approval.get("file_url"):
                file_display_name = approval["custom_file_name"] or approval["file_url"].split('/')[-1]
                detail_blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Attachments:* <{approval['file_url']}|{file_display_name}>"
                        }
                    }
                )

            if approval["type"] == "time_off":
                detail_blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Time Off Request*\n\n*Employee Name:* <@{approval['employee']}>\n*Requested On:* {approval['request_date']}\n*Request Type:* {approval['request_type']}\n*Time Requested:* {approval['time_requested']}\n*Summary:* {approval['summary']} days\n*Notes:* {approval['notes']}"
                        }
                    }
                ]

            if approval.get("image_url"):
                detail_blocks[0]["accessory"] = {
                    "type": "image",
                    "image_url": approval["image_url"],
                    "alt_text": "Approval Image"
                }

            client.views_open(
                trigger_id=body["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": f"view_details_modal-{approval_id}",
                    "title": {
                        "type": "plain_text",
                        "text": "Details"
                    },
                    "blocks": detail_blocks
                }
            )
            break

@app.action("overflow")
def handle_overflow(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    action_value = body["actions"][0]["selected_option"]["value"]
    action, approval_id = action_value.split('-')
    logger.debug(f"Overflow action: {action} for approval {approval_id} by user: {user_id}")
    global approvals
    if action == "revert":
        for approval in approvals:
            if approval["id"] == approval_id:
                approval["status"] = "pending"
                break
    elif action == "edit":
        for approval in approvals:
            if approval["id"] == approval_id:
                if approval["type"] == "expense":
                    client.views_open(
                        trigger_id=body["trigger_id"],
                        view={
                            "type": "modal",
                            "callback_id": f"edit_approval_modal-{approval_id}",
                            "title": {
                                "type": "plain_text",
                                "text": "Edit Approval"
                            },
                            "blocks": [
                                {
                                    "type": "input",
                                    "block_id": "title_input",
                                    "element": {
                                        "type": "plain_text_input",
                                        "action_id": "title",
                                        "initial_value": approval["title"] or ""
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Title"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "requestor_input",
                                    "element": {
                                        "type": "users_select",
                                        "action_id": "requestor",
                                        "initial_user": approval["requestor"]
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Requestor"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "amount_input",
                                    "element": {
                                        "type": "plain_text_input",
                                        "action_id": "amount",
                                        "initial_value": approval["amount"] or ""
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Requested Amount"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "total_input",
                                    "element": {
                                        "type": "plain_text_input",
                                        "action_id": "total",
                                        "initial_value": approval["total"] or ""
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Report Total"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "date_input",
                                    "element": {
                                        "type": "datepicker",
                                        "action_id": "date",
                                        "initial_date": approval["date"]
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Report Date"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "employee_input",
                                    "element": {
                                        "type": "users_select",
                                        "action_id": "employee",
                                        "initial_user": approval["employee"]
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Employee Name"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "file_input",
                                    "element": {
                                        "type": "plain_text_input",
                                        "action_id": "file_url",
                                        "initial_value": approval["file_url"] or ""
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "File URL"
                                    },
                                    "optional": True
                                },
                                {
                                    "type": "input",
                                    "block_id": "custom_file_name_input",
                                    "element": {
                                        "type": "plain_text_input",
                                        "action_id": "custom_file_name",
                                        "initial_value": approval["custom_file_name"] or ""
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Custom File Name"
                                    },
                                    "optional": True
                                },
                                {
                                    "type": "input",
                                    "block_id": "image_url_input",
                                    "element": {
                                        "type": "plain_text_input",
                                        "action_id": "image_url",
                                        "initial_value": approval["image_url"] or ""
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Image URL"
                                    },
                                    "optional": True
                                }
                            ],
                            "submit": {
                                "type": "plain_text",
                                "text": "Update"
                            }
                        }
                    )
                elif approval["type"] == "time_off":
                    client.views_open(
                        trigger_id=body["trigger_id"],
                        view={
                            "type": "modal",
                            "callback_id": f"edit_approval_modal-{approval_id}",
                            "title": {
                                "type": "plain_text",
                                "text": "Edit Time Off"
                            },
                            "blocks": [
                                {
                                    "type": "input",
                                    "block_id": "employee_input",
                                    "element": {
                                        "type": "users_select",
                                        "action_id": "employee",
                                        "initial_user": approval["employee"]
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Employee Name"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "request_date_input",
                                    "element": {
                                        "type": "datepicker",
                                        "action_id": "request_date",
                                        "initial_date": approval["request_date"]
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Requested On"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "start_date_input",
                                    "element": {
                                        "type": "datepicker",
                                        "action_id": "start_date",
                                        "initial_date": approval["time_requested"].split(" to ")[0]
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Start Date"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "end_date_input",
                                    "element": {
                                        "type": "datepicker",
                                        "action_id": "end_date",
                                        "initial_date": approval["time_requested"].split(" to ")[1]
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "End Date"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "request_type_input",
                                    "element": {
                                        "type": "plain_text_input",
                                        "action_id": "request_type",
                                        "initial_value": approval["request_type"]
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Request Type"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "notes_input",
                                    "element": {
                                        "type": "plain_text_input",
                                        "action_id": "notes",
                                        "initial_value": approval["notes"]
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Notes"
                                    }
                                },
                                {
                                    "type": "input",
                                    "block_id": "image_url_input",
                                    "element": {
                                        "type": "plain_text_input",
                                        "action_id": "image_url",
                                        "initial_value": approval["image_url"] or ""
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "Image URL"
                                    },
                                    "optional": True
                                }
                            ],
                            "submit": {
                                "type": "plain_text",
                                "text": "Update"
                            }
                        }
                    )
                break
    elif action == "delete":
        approvals = [approval for approval in approvals if approval["id"] != approval_id]
    update_home_tab(client, {"user": user_id})

@app.view("new_expense_approval_modal")
def handle_new_expense_approval_submission(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    state_values = body["view"]["state"]["values"]
    new_approval = {
        "id": generate_approval_id(),
        "title": state_values["title_input"]["title"]["value"],
        "requestor": state_values["requestor_input"]["requestor"]["selected_user"],
        "amount": state_values["amount_input"]["amount"]["value"],
        "total": state_values["total_input"]["total"]["value"],
        "date": state_values["date_input"]["date"]["selected_date"],
        "employee": state_values["employee_input"]["employee"]["selected_user"],
        "status": "pending",
        "file_url": state_values["file_input"]["file_url"]["value"] if "file_input" in state_values else "",
        "custom_file_name": state_values["custom_file_name_input"]["custom_file_name"]["value"] if "custom_file_name_input" in state_values else "",
        "image_url": state_values["image_url_input"]["image_url"]["value"] if "image_url_input" in state_values else "",
        "type": "expense",
        "home_ts": ""
    }
    approvals.append(new_approval)
    update_home_tab(client, {"user": user_id})

@app.view("new_time_off_approval_modal")
def handle_new_time_off_approval_submission(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    state_values = body["view"]["state"]["values"]
    start_date = datetime.strptime(state_values["start_date_input"]["start_date"]["selected_date"], "%Y-%m-%d")
    end_date = datetime.strptime(state_values["end_date_input"]["end_date"]["selected_date"], "%Y-%m-%d")
    days_requested = (end_date - start_date).days + 1

    new_approval = {
        "id": generate_approval_id(),
        "title": "Time Off Request",
        "requestor": user_id,
        "request_date": state_values["request_date_input"]["request_date"]["selected_date"],
        "request_type": state_values["request_type_input"]["request_type"]["value"],
        "time_requested": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "summary": str(days_requested),
        "notes": state_values["notes_input"]["notes"]["value"],
        "employee": state_values["employee_input"]["employee"]["selected_user"],
        "status": "pending",
        "image_url": state_values["image_url_input"]["image_url"]["value"] if "image_url_input" in state_values else "",
        "type": "time_off",
        "home_ts": ""
    }
    approvals.append(new_approval)
    update_home_tab(client, {"user": user_id})

# Dynamic handler for edit approval modals
@app.view(re.compile(r"edit_approval_modal-\d+"))
def handle_edit_approval_submission(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    state_values = body["view"]["state"]["values"]
    approval_id = body["view"]["callback_id"].split('-')[-1]
    for approval in approvals:
        if approval["id"] == approval_id:
            if approval["type"] == "expense":
                approval["title"] = state_values["title_input"]["title"]["value"]
                approval["requestor"] = state_values["requestor_input"]["requestor"]["selected_user"]
                approval["amount"] = state_values["amount_input"]["amount"]["value"]
                approval["total"] = state_values["total_input"]["total"]["value"]
                approval["date"] = state_values["date_input"]["date"]["selected_date"]
                approval["employee"] = state_values["employee_input"]["employee"]["selected_user"]
                approval["file_url"] = state_values["file_input"]["file_url"]["value"] if "file_input" in state_values else ""
                approval["custom_file_name"] = state_values["custom_file_name_input"]["custom_file_name"]["value"] if "custom_file_name_input" in state_values else ""
                approval["image_url"] = state_values["image_url_input"]["image_url"]["value"] if "image_url_input" in state_values else ""
            elif approval["type"] == "time_off":
                start_date = datetime.strptime(state_values["start_date_input"]["start_date"]["selected_date"], "%Y-%m-%d")
                end_date = datetime.strptime(state_values["end_date_input"]["end_date"]["selected_date"], "%Y-%m-%d")
                days_requested = (end_date - start_date).days + 1

                approval["request_date"] = state_values["request_date_input"]["request_date"]["selected_date"]
                approval["request_type"] = state_values["request_type_input"]["request_type"]["value"]
                approval["time_requested"] = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                approval["summary"] = str(days_requested)
                approval["notes"] = state_values["notes_input"]["notes"]["value"]
                approval["employee"] = state_values["employee_input"]["employee"]["selected_user"]
                approval["image_url"] = state_values["image_url_input"]["image_url"]["value"] if "image_url_input" in state_values else ""
            break
    update_home_tab(client, {"user": user_id})

@app.action("filter_approvals")
def handle_filter_approvals(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    selected_filter = body["actions"][0]["selected_option"]["value"]
    logger.debug(f"Filter selected: {selected_filter} by user: {user_id}")
    view = home_tab_view(client, approvals, selected_filter)
    try:
        response = client.views_publish(user_id=user_id, view=view)
        logger.debug(f"Home tab updated with filtered approvals: {response['ts']}")
    except Exception as e:
        logger.error(f"Error publishing filtered home tab: {e}")

@app.action("actions_overflow")
def handle_actions_overflow(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    selected_option = body["actions"][0]["selected_option"]["value"]
    logger.debug(f"Action selected: {selected_option} by user: {user_id}")
    if selected_option == "new_approval":
        trigger_id = body["trigger_id"]
        client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "new_approval_modal",
                "title": {
                    "type": "plain_text",
                    "text": "New Approval"
                },
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "type_input",
                        "element": {
                            "type": "static_select",
                            "action_id": "type",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select approval type"
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Expense"
                                    },
                                    "value": "expense"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Time Off"
                                    },
                                    "value": "time_off"
                                }
                            ]
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Approval Type"
                        }
                    }
                ],
                "submit": {
                    "type": "plain_text",
                    "text": "Next"
                }
            }
        )
    elif selected_option == "edit_approval":
        # Handle the edit approval option
        pass

@app.view("new_approval_modal")
def handle_new_approval_type_selection(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    state_values = body["view"]["state"]["values"]
    approval_type = state_values["type_input"]["type"]["selected_option"]["value"]
    
    if approval_type == "expense":
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "new_expense_approval_modal",
                "title": {
                    "type": "plain_text",
                    "text": "New Expense Approval"
                },
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "title_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "title"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Title"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "requestor_input",
                        "element": {
                            "type": "users_select",
                            "action_id": "requestor"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Requestor"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "amount_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "amount"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Requested Amount"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "total_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "total"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Report Total"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "date_input",
                        "element": {
                            "type": "datepicker",
                            "action_id": "date"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Report Date"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "employee_input",
                        "element": {
                            "type": "users_select",
                            "action_id": "employee"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Employee Name"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "file_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "file_url"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "File URL"
                        },
                        "optional": True
                    },
                    {
                        "type": "input",
                        "block_id": "custom_file_name_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "custom_file_name"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Custom File Name"
                        },
                        "optional": True
                    },
                    {
                        "type": "input",
                        "block_id": "image_url_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "image_url"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Image URL"
                        },
                        "optional": True
                    }
                ],
                "submit": {
                    "type": "plain_text",
                    "text": "Create"
                }
            }
        )
    elif approval_type == "time_off":
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "new_time_off_approval_modal",
                "title": {
                    "type": "plain_text",
                    "text": "New Time Off Approval"
                },
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "employee_input",
                        "element": {
                            "type": "users_select",
                            "action_id": "employee"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Employee Name"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "request_date_input",
                        "element": {
                            "type": "datepicker",
                            "action_id": "request_date"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Requested On"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "start_date_input",
                        "element": {
                            "type": "datepicker",
                            "action_id": "start_date"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Start Date"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "end_date_input",
                        "element": {
                            "type": "datepicker",
                            "action_id": "end_date"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "End Date"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "request_type_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "request_type"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Request Type"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "notes_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "notes"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Notes"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "image_url_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "image_url"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Image URL"
                        },
                        "optional": True
                    }
                ],
                "submit": {
                    "type": "plain_text",
                    "text": "Create"
                }
            }
        )

# Start the app
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
