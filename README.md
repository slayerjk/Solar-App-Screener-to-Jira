===Purpose===

The purpose off script is to automatization of Jira tickets creation basing on last scan's reports.

===Data & Workflow===

- SAS API URLS
- SAS POST ENDLESS TOKEN(YOU MUST USE WITH TEMPORARY TOKEN OF THIS USER FIRST): http://<sas-ip>/app/api/v1/user/token/endless; to body(x-www-form-urlencoded: password <xxxx>)
- SAS API ROOT: http://<sas-ip>/app/api/v1
- SAS GET ALL PROJECTS: <root>/projects
- SAS POST START SCAN: <root>/scan/start
- SAS GET LAST SCAN DETAILS: <root>/projects/filtered
- SAS POST SCAN'S REPORT ZIP: <root>/report/file
- SAS POST CREATE JIRA TASK: <root>/jira/task
- SAS GET ISSUE'S JIRA TASKS: <root>/issues/<issue-id>/jira/tasks
- SAS GET ALL SCAN'S ISSUES WITH MEDIUM&HIGH LEVELS: <root>/scans/<sas_scan_uuid>/vulnerabilities/filtered

===Templates for POST===
	
Create Jira Task via SAS Template:

```
{
    "parent": "",
    "type": 10002,
    "key": "<YOUR JIRA PROJECT KEY>",
    "priority": 0,
    "components": [],
	"summary": "$summary",
    "description": "",
    "user": "",
    "issue": "",
    "configuration": "{\"summary\":\"$summary\",\"issuetype\":\"$issuetype\",\"project\":\"$project\",\"description\":\"$description\",\"priority\":\"$priority\"}"
}
```

**Create Jira Task via SAS Template**:
```
{
    "parent": "",
    "type": 10002,
    "key": "<YOUR JIRA PROJECT KEY>",
    "priority": 0,
    "components": [],
	"summary": "$summary",
    "description": "",
    "user": "",
    "issue": "",
    "configuration": "{\"summary\":\"$summary\",\"issuetype\":\"$issuetype\",\"project\":\"$project\",\"description\":\"$description\",\"priority\":\"$priority\"}"
}
```

**Download SAS Report Archive Template**:
```
{
    "projectUuid": "<YOUR SAS PROJECT UUID>",
    "scanUuids": [
        ""
    ],
    "exportSettings": {
        "uuid": "system_template_settings_uuid",
        "projectInfoSettings": {
            "securityLevelDynamics": true,
            "vulnNumberDynamics": true,
            "scanHistory": 0
        },
        "sort": "CR",
        "scanInfoSettings": {
            "included": true,
            "foundVulnChart": true,
            "typeVulnChart": true,
            "langStats": true,
            "fileStats": false,
            "scanErrorInfo": true,
            "scanSettings": true
        },
        "filterSettings": {
            "critical": true,
            "medium": true,
            "low": false,
            "info": false,
            "standardLibs": true,
            "classFiles": true,
            "waf": true,
            "jira": true,
            "fuzzy": {
                "included": false,
                "critical": 4,
                "medium": 4,
                "low": 4,
                "info": 4,
                "percentile": 10,
                "mode": "TRUE"
            },
            "lang": "ABAP,ANDROID,APEX,CS,CCPP,COBOL,CONFIG,DART,DELPHI,GO,GROOVY,HTML5,JAVA,JAVASCRIPT,KOTLIN,LOTUS,OBJC,PASCAL,PHP,PLSQL,PYTHON,PERL,RUBY,RUST,SCALA,SOLIDITY,SWIFT,TSQL,TYPESCRIPT,VBNET,VBA,VBSCRIPT,VB,VYPER,ONES"
        },
        "tableSettings": {
            "included": true,
            "entriesSettings": {
                "notProcessed": true,
                "confirmed": true,
                "rejected": false
            },
            "entryNum": 0
        },
        "detailedResultsSettings": {
            "included": true,
            "entriesSettings": {
                "notProcessed": true,
                "confirmed": true,
                "rejected": false
            },
            "entryNum": 0,
            "comment": true,
            "jiraInfo": true,
            "traceNum": 1,
            "sourceCodeNum": 3
        },
        "wafSettings": {
            "included": true,
            "entriesSettings": {
                "notProcessed": true,
                "confirmed": true,
                "rejected": false
            },
            "imperva": true,
            "mod": true,
            "f5": true
        },
        "generalSettings": {
            "reportSettings": true,
            "contents": true,
            "locale": "ru",
            "format": "CSV"
        }
    },
    "comparisonSettings": {
        "included": false,
        "scanUuid": "",
        "newIssue": true,
        "saved": true,
        "fixed": false,
        "entryNum": 0,
        "scanSettings": true
    }
}
```

Also you'll need "sas-api-token.txt" file in sas_files folder.
