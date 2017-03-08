from jira import JIRA
from slackbot.bot import respond_to
import json
import dateutil.parser
import os
import requests
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
zipcodeURL = 'https://www.zipcodeapi.com/rest/S3OFY3cNv0FoOM4d6Fq5RyXkaSiQUwoNActzgFnLF3auPeIWT81LHZ6RRpILV6yw/radius.json/%s/%s/mile'

def is_admin(user):
    if user == 'D44H7U0HM' or user == 'C38NCTQQ1':
        return True
    return False


@respond_to("""jira photographer (\\b\d{5}\\b)""")
def jira_photographer_zip(message, zipcode):
    jira = authenticate()
    radius = "25"
    response = requests.get(zipcodeURL % (zipcode, radius))
    str_list = []
    if response.status_code == 200:
        data = response.json()
        if len(data) > 0:
            for zip in data['zip_codes']:
                str_list.append("""'Zip Code' ~ %s""" % zip['zip_code'])
    zips = ' OR '.join(str_list)
    photographers = get_photographers(jira, zips)
    response = formatter.photographer_list(photographers, zipcode, "25")
    message.reply_webapi('Photographers', attachments=json.dumps(response))


@respond_to('jira onboard (.*)')
def jira_onboard(message, location_id):
    jira = authenticate()
    response = formatter.location_summary(get_all_onboard_issues(jira, location_id), "Location ID", location_id)
    message.reply_webapi('Onboard Summary', attachments=json.dumps(response))


@respond_to('jira location (.*)')
def jira_location(message, location_id):
    jira = authenticate()
    response = formatter.search_results(get_all_jira_issues(jira, location_id))
    message.reply_webapi('Location Summary', attachments=json.dumps(response))

@respond_to('jira gift_link (.*)')
def jira_gift_link(message, location_id):
   if is_admin(message.body['channel']):
       jira = authenticate();
       issueDict = get_all_gifted_photoshoot_issues(jira, location_id)
       jira.create_issue_link('Gifted Photoshoot to Identity Refresh',
                              issueDict[gifted_photoshoot_id].key, issueDict[identity_refresh_id])
       jira.create_issue_link('Gifted Photoshoot to Platform Refresh',
                              issueDict[gifted_photoshoot_id].key, issueDict[platform_refresh_id])
       jira.create_issue_link('Identity Refresh to Platform Refresh',
                              issueDict[identity_refresh_id].key, issueDict[platform_refresh_id])
       response = formatter.search_results(issueDict.values())
       message.reply_webapi('Gifting Photoahoot Summary', attachments=json.dumps(response))
   else:
       message.reply_webapi('Need to be an admin or in an admin channel to ask for that.')

@respond_to('jira onboard_link (.*)')
def jira_onboard_link(message, location_id):
   if is_admin(message.body['channel']):
       jira = authenticate();
       issueDict = get_all_onboard_issues(jira, location_id)
       jira.create_issue_link('Platform Audit to Credentials', issueDict[platform_audit_id].key,
                              issueDict[credentials_id])
       jira.create_issue_link('Platform Audit to Platform Setup', issueDict[platform_audit_id].key,
                              issueDict[platform_setup_id])
       jira.create_issue_link('Platform Audit to Customer Voice', issueDict[platform_audit_id].key,
                              issueDict[customer_voice_id])
       jira.create_issue_link('Platform Audit to Photoshoot', issueDict[platform_audit_id].key,
                              issueDict[photoshoot_id])
       jira.create_issue_link('Credentials to Platform Setup', issueDict[credentials_id].key,
                              issueDict[platform_setup_id])
       jira.create_issue_link('Credentials to Customer Voice', issueDict[credentials_id].key,
                              issueDict[customer_voice_id])
       jira.create_issue_link('Credentials to Photoshoot', issueDict[credentials_id].key,
                              issueDict[photoshoot_id])
       jira.create_issue_link('Photoshoot to Platform Setup', issueDict[photoshoot_id].key,
                              issueDict[platform_setup_id])
       jira.create_issue_link('Photoshoot to Customer Voice', issueDict[photoshoot_id].key,
                              issueDict[customer_voice_id])
       jira.create_issue_link('Customer Voice to Platform Setup', issueDict[customer_voice_id].key,
                              issueDict[platform_setup_id])
       response = formatter.location_summary(get_all_onboard_issues(jira, location_id), "Location ID", location_id)
       message.reply_webapi('Onboard Summary', attachments=json.dumps(response))
   else:
       message.reply_webapi('Need to be an admin or in an admin channel to ask for that.')

@respond_to('jira sf (.*)')
def jira_sf(message, sfid):
    jira = authenticate()
    response = formatter.location_summary(get_all_issues_salesforce_id(jira, sfid), "Salesforce ID", sfid)
    message.reply_webapi('Location Summary', attachments=json.dumps(response))


@respond_to('jira (PLATFORM\W[0-9]*|STUDIO\W[0-9]*)')
def jira_issue(message, key):
    jira = authenticate()
    response = formatter.issue_summary(jira, key)
    message.reply_webapi('Issue Summary', attachments=json.dumps(response))


@respond_to('help')
def help(message):
    text = """*help:* Displays this message
*onboard <location id>:* Displays a summary of the 5 onboarding issues
*sf <salesforce id>:* Displays a summary of the 5 onboarding issues
*location <location id>:* Displays a list of all issues associated with a Location ID
*<issue key>:* Displays a summary of the input issue"""

    if is_admin(message.body['channel']):
        text += """\n\nADMIN COMMANDS
*onboard_link <location id>:* links the 5 onboarding tickets
*gift_link <location id>:* links the 3 Photoshoot gifting tickets"""

    message.reply_webapi('Help Menu', attachments= [{
        "fallback": "Ugh. I don't know what you are asking for. Try 'jira help'",
        "color": "ADD8E6",
        "title": "Commands you can use to get JIRA information:",
        "text": text,
        "mrkdwn_in": ["text", "pretext", "fields"],
    }])


def authenticate():
    return JIRA({'server': os.environ.get('JIRA_SERVER')},
                basic_auth=(os.environ.get('JIRA_USERNAME'), os.environ.get('JIRA_PASSWORD')))


def get_all_issues_salesforce_id(jira, sfid):
    issues = jira.search_issues(
        """project in (PLATFORM,STUDIO) AND
        AND issuetype in ('Platform Audit', Credentials, 'Platform Setup', 'Customer Voice', 'Photoshoot')
        'Salesforce ID' ~ '%s'""" % sfid)
    return {str(issue.fields.issuetype.id): issue for issue in issues}


def get_all_onboard_issues(jira, location_id):
    issues = jira.search_issues("""project in (PLATFORM,STUDIO)
     AND issuetype in ('Platform Audit', Credentials, 'Platform Setup', 'Customer Voice', 'Photoshoot')
     AND 'Location ID' ~ %s""" % location_id)
    return {str(issue.fields.issuetype.id): issue for issue in issues}


def get_all_jira_issues(jira, location_id):
    issues = jira.search_issues("""project in (PLATFORM,STUDIO)
     AND 'Location ID' ~ %s ORDER BY created ASC""" % location_id)
    return issues

def get_all_gifted_photoshoot_issues(jira, location_id):
    issues = jira.search_issues(
        """project in (PLATFORM,STUDIO) AND issuetype in ('Gifted Photoshoot', 'Identity Refresh', 'Platform Refresh') AND 'Location ID' ~ '%s'""" % location_id)
    return {str(issue.fields.issuetype.id): issue for issue in issues}


def get_photographers(jira, zip_clause):
    jql = """project = STUDIO and issuetype = Photographer AND status = Approved and (%s)""" % zip_clause
    issues = jira.search_issues(jql)
    return issues


class formatter:
    issue_url = """https://msh-success.atlassian.net/browse/%s"""

    @staticmethod
    def build_link(url, text):
        if formatter.should_jira_link():
            return "<%s|%s>" % (url, text)
        return text

    @staticmethod
    def should_jira_link():
        should_link = os.environ.get('CREATE_JIRA_LINKS')
        if should_link is not None and should_link == "YES":
            return True
        return False

    @staticmethod
    def get_issuetype(issue):
        return issue.fields.issuetype.name

    @staticmethod
    def get_issue_link(issue):
        if formatter.should_jira_link():
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
    def get_selectlist(issue, fieldname, default="<none>"):
        if getattr(issue.fields, fieldname) is None:
            return default
        return getattr(issue.fields, fieldname).value

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
        str_list.append(""">*Assignee:* %s\n""" % formatter.get_assignee(issue))
        str_list.append(""">*Status:* %s\n""" % issue.fields.status.name)
        str_list.append(""">*Last Updated:* %s\n""" % formatter.get_date_time(issue.fields.updated))
        issuetype = formatter.get_issuetype(issue)

        if issuetype == "Platform Audit":
            str_list.append(
                ">*In Progress Timestamp: * %s\n" % formatter.get_date_time(issue.fields.customfield_10808))
        elif issuetype == "Photoshoot" or issuetype == "Gifted Photoshoot":
            str_list.append(""">*Photoshoot?:* %s\n""" % formatter.get_selectlist(issue, "customfield_10400"))
            str_list.append(""">*Resolution:* %s\n""" % issue.fields.resolution)
            str_list.append(""">*Pixieset URL:* <%s|link>\n""" % issue.fields.customfield_10208)
            str_list.append(
                ">*Photoshoot Date: * %s\n" % formatter.get_date_time(issue.fields.customfield_10205))
            str_list.append(
                ">*Scheduled Timestamp: * %s\n" % formatter.get_date_time(issue.fields.customfield_11403))
            str_list.append(
                ">*Last Scheduled Timestamp: * %s\n" % formatter.get_date_time(issue.fields.customfield_12900))
            str_list.append(
                ">*Photoshoot Complete Timestamp: * %s\n" % formatter.get_date_time(issue.fields.customfield_11701))
        elif issuetype == "Customer Voice":
            str_list.append(""">*Passport URL:* <%s|link>\n""" % issue.fields.customfield_10210)
            str_list.append(""">*Credentials Complete:* %s\n""" % formatter.get_selectlist(issue, "customfield_11704"))
            str_list.append(""">*Approval Timestamp:* %s\n\n""" % formatter.get_date_time(issue.fields.customfield_11405))
            str_list.append(""">*Brand Kit Updates:*\n""")

            str_list.append(""">*Brand Kit Updates:*\n""")
        elif issuetype == "Credentials":
            str_list.append(""">*Facebook:* %s\n""" % formatter.get_selectlist(issue, "customfield_10804"))
            str_list.append(""">*Twitter:* %s\n""" % formatter.get_selectlist(issue, "customfield_10507"))
            str_list.append(""">*Instagram:* %s\n""" % formatter.get_selectlist(issue, "customfield_12511"))
            str_list.append(""">*Google:* %s\n""" % formatter.get_selectlist(issue, "customfield_10510"))
            str_list.append(""">*Yelp:* %s\n""" % formatter.get_selectlist(issue, "customfield_10513"))
            str_list.append(""">*Foursquare:* %s\n""" % formatter.get_selectlist(issue, "customfield_10809"))
            str_list.append(""">*TripAdvisor:* %s\n""" % formatter.get_selectlist(issue, "customfield_10516"))
        elif issuetype == "Platform Setup":
            str_list.append(""">*Facebook:* %s\n""" % formatter.get_selectlist(issue, "customfield_10504"))
            str_list.append(""">*Twitter:* %s\n""" % formatter.get_selectlist(issue, "customfield_10157"))
            str_list.append(""">*Instagram:* %s\n""" % formatter.get_selectlist(issue, "customfield_12510"))
            str_list.append(""">*Google:* %s\n""" % formatter.get_selectlist(issue, "customfield_10161"))
            str_list.append(""">*Yelp:* %s\n""" % formatter.get_selectlist(issue, "customfield_10158"))
            str_list.append(""">*Foursquare:* %s\n""" % formatter.get_selectlist(issue, "customfield_10159"))
            str_list.append(""">*TripAdvisor:* %s\n""" % formatter.get_selectlist(issue, "customfield_10160"))
        elif issuetype == "Identity Refresh":
            str_list.append(""">*Passport URL:* <%s|link>\n""" % issue.fields.customfield_10210)
        elif issuetype == "Platform Refresh":
            str_list.append(""">*Due Date:* %s\n""" % formatter.get_date_time(issue.fields.duedate))

        return ''.join(str_list)

    @staticmethod
    def short_summary(issue):
        str_list = []
        str_list.append(""">*Status: * %s\n""" % formatter.build_link(formatter.get_issue_link(issue), issue.fields.status.name))
        str_list.append(""">*Updated: * %s\n""" % formatter.get_date_time(issue.fields.updated))
        str_list.append(""">*Assignee: * %s\n""" % formatter.get_assignee(issue))
        return ''.join(str_list)

    @staticmethod
    def search_results(issues):
        counter = 0;
        str_list = []
        name = ""
        for issue in issues:
            counter += 1
            if counter > 10:
                break;
            if name == "":
                name = issue.fields.summary
            str_list.append("""*%s* %s (%s): Updated: %s\n""" % (formatter.get_issuetype(issue),
                                                      formatter.build_link(formatter.get_issue_link(issue), issue.key),
                                                      issue.fields.status.name,
                                                      formatter.get_date_time(issue.fields.updated)))

        return [{
            "fallback": "Results",
            "pretext": "Results",
            "color": "#36a64f",
            "title": "%s - %d issues" % (name, len(issues)),
            "text": ''.join(str_list),
            "mrkdwn_in": ["text", "pretext", "fields"]
        }]

    @staticmethod
    def photographer_list(issues, zip, radius):
        str_list = []
        for issue in issues:
            str_list.append("""*%s* %s\n""" % (issue.fields.summary,
                                                                 formatter.build_link(formatter.get_issue_link(issue),
                                                                                      issue.key)))

        return [{
            "fallback": "Results",
            "pretext": "Results",
            "color": "#36a64f",
            "title": "Photographers within %s miles of %s" % (radius, zip),
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