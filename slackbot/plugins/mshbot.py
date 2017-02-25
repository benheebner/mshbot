from jira import JIRA
from slackbot.bot import respond_to
import json
import dateutil.parser
import os
from slackbot.bot import listen_to
import re

credentials_id = '10004'
platform_audit_id = '10002'
platform_setup_id = '10003'
customer_voice_id = '10009'
photoshoot_id = '10007'
contact_id = '10201'
brand_kit_update_id = '10300'
gifted_photoshoot_id = '10800'
identity_refresh_id = '10802'
platform_refresh_id = '10801'
transition_photoshoot_ready = '121'
transition_credential_ready = '11'
transition_platform_audit_resolve = '61'
transition_credentials_resolve = '61'
transition_customer_voice_resolve = '61'
transition_platform_setup_resolve = '61'
transition_photoshoot_done = '11'
transition_contact_resolve = '31'
transition_followup_resolve = '31'
transition_brandkitupdate_resolve = '111'
salesforce_custom_field_id = 'customfield_10221'
resolution_id_customer_cancelled = '10200'
resolution_id_photoshoot_not_offered = '10400'
resolution_id_photoshoot_opted_out = '10100'
link_id_blocks = '10000'


@respond_to('jira onboard (.*)')
def jira_location(message, location_id):
    jira = authenticate()
    response = formatter.location_summary(get_all_onboard_issues(jira, location_id), "Location ID", location_id)
    message.reply_webapi('Onboard Summary', attachments=json.dumps(response))


@respond_to('jira jira (.*)')
def jira_location(message, location_id):
    jira = authenticate()
    response = formatter.location_summary(get_all_jira_issues(jira, location_id), "Location ID", location_id)
    message.reply_webapi('Location Summary', attachments=json.dumps(response))


@respond_to('jira sf (.*)')
def jira_location(message, sfid):
    jira = authenticate()
    response = formatter.location_summary(get_all_issues_salesforce_id(jira, sfid), "Salesforce ID", sfid)
    message.reply_webapi('Location Summary', attachments=json.dumps(response))


@respond_to('jira (PLATFORM\W[0-9]*|STUDIO\W[0-9]*)')
def jira_location(message, key):
    jira = authenticate()
    response = formatter.issue_summary(jira, key)
    message.reply_webapi('Issue Summary', attachments=json.dumps(response))


@respond_to('help')
def help(message):
    message.reply_webapi('Issue Summary', attachments= [{
        "fallback": "Ugh. I don't know what you are asking for. Try 'jira help'",
        "color": "ADD8E6",
        "title": "Commands you can use to get JIRA information:",
        "text": """*help:* Displays this message
*location <location id>:* Displays a summary of the 5 onboarding issues
*sf <salesforce id>:* Displays a summary of the 5 onboarding issues
*<issue key>:* Displays a summary of the input issue""",
        "mrkdwn_in": ["text", "pretext", "fields"],
    }])


def authenticate():
    return JIRA({'server': os.environ.get('JIRA_SERVER')},
                basic_auth=(os.environ.get('JIRA_USERNAME'), os.environ.get('JIRA_PASSWORD')))


def get_all_issues_salesforce_id(jira, sfid):
    issues = jira.search_issues(
        """project in (PLATFORM,STUDIO) AND 'Salesforce ID' ~ '%s'""" % sfid)
    return {str(issue.fields.issuetype.id): issue for issue in issues}


def get_all_onboard_issues(jira, location_id):
    issues = jira.search_issues("""project in (PLATFORM,STUDIO)
     AND issuetype in ('Platform Audit', Credentials, 'Platform Setup', 'Customer Voice', 'Photoshoot')
     AND 'Location ID' ~ %s""" % location_id)
    return {str(issue.fields.issuetype.id): issue for issue in issues}


def get_all_jira_issues(jira, location_id):
    issues = jira.search_issues("""project in (PLATFORM,STUDIO)
     AND 'Location ID' ~ %s""" % location_id)
    return {str(issue.fields.issuetype.id): issue for issue in issues}


class formatter:
    issue_url = """https://msh-success.atlassian.net/browse/%s"""

    @staticmethod
    def build_link(url, text):
        if formatter.should_jira_link(url):
            return "<%s|%s>" % (url, text)
        return text

    @staticmethod
    def should_jira_link(url):
        if 'atlassian' not in url:
            return True
        should_link = os.environ.get('CREATE_JIRA_LINKS')
        if should_link is not None and should_link == "YES":
            return True
        return False

    @staticmethod
    def get_issuetype(issue):
        return issue.fields.issuetype.name

    @staticmethod
    def get_issue_link(issue):
        if formatter.should_jira_link(issue.self):
            return formatter.issue_url % issue.key
        return ""

    @staticmethod
    def get_date_time(field):
        if field is not None:
            return dateutil.parser.parse(field).strftime("%B %-d at %-I:%M %p")
        else:
            return "<none>"

    @staticmethod
    def get_assignee(issue):
        if issue.fields.assignee is None:
            return "Unassigned"
        else:
            return issue.fields.assignee.displayName

    @staticmethod
    def issue_summary(jira, key):
        issue = jira.issue(key)
        return [{
            "fallback": "Information for %s" % issue.fields.summary,
            "pretext": "Information for %s" % issue.fields.summary,
            "color": "#36a64f",
            "title": "%s: %s" % (formatter.get_issuetype(issue), issue.fields.summary),
            "title_link": formatter.get_issue_link(issue),
            "text": formatter.long_summary(issue),
            "mrkdwn_in": ["text", "pretext", "fields"],
            "thumb_url": issue.fields.issuetype.iconUrl,
            "footer": "Updated: %s" % formatter.get_date_time(issue.fields.updated)
        }]

    @staticmethod
    def long_summary(issue):
        str_list = []
        str_list.append(""">*Assignee: * %s\n""" % formatter.get_assignee(issue))
        str_list.append(""">*Status: * %s\n""" % issue.fields.status.name)

        if formatter.get_issuetype(issue) == "Platform Audit":
            str_list.append(""">*Offer Photoshoot:* %s\n""" % issue.fields.customfield_10212.value)
            str_list.append(""">*Facebook Presence:* %s\n""" % issue.fields.customfield_10502.value)
            str_list.append(""">*Twitter Presence:* %s\n""" % issue.fields.customfield_10505.value)
            str_list.append(""">*Google Presence:* %s\n""" % issue.fields.customfield_10508.value)
            str_list.append(""">*Foursquare Presence:* %s\n""" % issue.fields.customfield_10517.value)
        elif formatter.get_issuetype(issue) == "Photoshoot":
            str_list.append(
                ">*Photoshoot Date: * %s\n" % formatter.get_date_time(issue.fields.customfield_10205))
        elif formatter.get_issuetype(issue) == "Customer Voice":
            str_list.append(""">*Approval Timestamp:* %s\n""" % formatter.get_date_time(issue.fields.customfield_11405))
        return ''.join(str_list)

    @staticmethod
    def short_summary(issue):
        str_list = []
        str_list.append(""">*Status:  *<%s|%s>\n""" % (formatter.get_issue_link(issue), issue.fields.status.name))
        str_list.append(""">*Updated: * %s\n""" % formatter.get_date_time(issue.fields.updated))
        str_list.append(""">*Assignee: * %s\n""" % formatter.get_assignee(issue))
        return ''.join(str_list)

    @staticmethod
    def search_results(issues):
        counter = 0;
        str_list = []
        for issue in issues:
            counter += 1
            if counter > 10:
                break;
            str_list.append("""<%s|%s>: %s\n""" % (formatter.get_issue_link(issue), issue.key, issue.fields.summary))

        return [{
            "fallback": "Results",
            "pretext": "Results",
            "color": "#36a64f",
            "title": "Found %d issues" % len(issues),
            "text": ''.join(str_list),
            "mrkdwn_in": ["text", "pretext", "fields"]
        }]

    @staticmethod
    def location_summary(issues, field, id):
        if len(issues) == 0:
            return [{
                "fallback": "No information exists for %s %s" % (field, id),
                "pretext": ">No information exists for %s %s" % (field, id),
                "mrkdwn_in": ["pretext"],
            }]

        business_name = issues[platform_audit_id].fields.summary
        audit = issues[platform_audit_id]
        creds = issues[credentials_id]
        setup = issues[platform_setup_id]
        cv = issues[customer_voice_id]
        photo = issues[photoshoot_id]
        location_id = audit.fields.customfield_10203

        return [{
            "fallback": "Onboarding Information for %s" % business_name,
            "pretext": "Onboarding Information for %s, Location ID: %s" % (business_name, location_id),
            "color": "#36a64f",
            "title": business_name,
            "fields": [
                {
                    "title": "Platform Audit: %s" % audit.key,
                    "value": formatter.short_summary(audit),
                    "short": "true"
                },
                {
                    "title": "",
                    "value": "",
                    "short": "true"
                },
                {
                    "title": "Credentials: %s" % creds.key,
                    "value": formatter.short_summary(creds),
                    "short": "true"
                },
                {
                    "title": "Photoshoot: %s" % photo.key,
                    "value": formatter.short_summary(photo),
                    "short": "false"
                },
                {
                    "title": "Customer Voice: %s" % cv.key,
                    "value": formatter.short_summary(cv),
                    "short": "false"
                },
                {
                    "title": "Platform Setup: %s" % setup.key,
                    "value": formatter.short_summary(setup),
                    "short": "false"
                }
            ],
            "mrkdwn_in": ["text", "pretext", "fields"]
        }]