from datetime import datetime

def _safe(d, *path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def _to_dt(x):
    if not x:
        return None
    fmts = ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y")
    for f in fmts:
        try:
            return datetime.strptime(x, f)
        except:
            pass
    return None

def _to_int(x):
    try:
        return int(x)
    except:
        return None

def _to_float(x):
    try:
        return float(x)
    except:
        return None

def build_procedure_document(j):
    case = _safe(j, "caseOverview", default={})
    mapdet = _safe(j, "mappingAndProcedureDetails", default={})
    abldet = _safe(j, "ablationDetails", default={})
    spa = _safe(j, "systemPerformanceAndErrorAnalysis", default={})

    doc = {
        "Procedur_id": _safe(j, "studyUID") or _safe(j, "lightningName"),
        "projectName": _safe(j, "projectName"),
        "cartoVersion": _safe(j, "cartoVersion"),
        "Country": _safe(j, "country"),
        "hospitalName": _safe(j, "hospitalName"),
        "workstationNumber": _safe(j, "workstationNumber"),
        "workstationModel": _safe(j, "workstationModel"),
        "generators": _safe(j, "generators"),
        "piuNum": _safe(j, "piuNum"),
        "lpNum": _safe(j, "lpNum"),
        "installDate": _safe(j, "installDate"),
        "uploadDate": _safe(j, "uploadDate"),
        "analysisDate": _safe(j, "analysisDate"),
        "lightningName": _safe(j, "lightningName"),
        "lightningDescription": _safe(j, "lightningDescription"),
        "studyLocation": _safe(j, "studyLocation"),
        "studyUID": _safe(j, "studyUID"),
        "studySize": _safe(j, "studySize"),
        "errorReportSize": _safe(j, "errorReportSize"),
        "studiesCount": _safe(j, "studiesCount"),
        "findings": _safe(case, "findings", default=[]),
        "procedureDate": _safe(case, "procedureDate"),
        "cathetersUsed": _safe(case, "cathetersUsed", default=[]),
        "targetedChamber": _safe(case, "targetedChamber"),
        "primaryArrhythmia": _safe(case, "primaryArrhythmia"),
        "secondaryArrhythmia": _safe(case, "secondaryArrhythmia"),
        "featuresInUse": _safe(case, "featuresInUse"),
        "licences": _safe(case, "licences"),
        "numberOfMapsCreated": _safe(mapdet, "numberOfMapsCreated"),
        "totalPointsCollected": _safe(mapdet, "totalPointsCollected"),
        "procedureTime": _safe(mapdet, "procedureTime"),
        "numberOfAblationSessions": _safe(abldet, "numberOfAblationSessions"),
        "totalAblationTime": _safe(abldet, "totalAblationTime"),
        "ablationType": _safe(abldet, "ablationType"),
        "Crash/Error Data": _safe(spa, "crashErrorData"),
        "Complaint ID": _safe(spa, "complaintID"),
        "Complaint Description": _safe(spa, "complaintDescription"),
        "Complaint From ECM": _safe(spa, "complaintFromECM"),
        "Screen Recordings": _safe(spa, "screenRecordings", default=[]),
        "User Bookmarks": _safe(spa, "userBookmarks", default=[]),
        "uniqueErrors": _safe(spa, "uniqueErrors") or _safe(j, "uniqueErrors"),
        "unclosedErrors": _safe(spa, "unclosedErrors", default=[]),
        "schemaVersion": 1,
    }

    cats = []
    for c in _as_list(doc.get("cathetersUsed")):
        cats.append({
            "catheterID": c.get("catheterID"),
            "name": c.get("name"),
            "partNumber": c.get("partNumber"),
            "lotNumber": c.get("lotNumber"),
            "connectionTimes": _as_list(c.get("connectionTimes"))
        })
    doc["cathetersUsed"] = cats

    doc["installDate"] = _to_dt(doc["installDate"])
    doc["uploadDate"] = _to_dt(doc["uploadDate"])
    doc["analysisDate"] = _to_dt(doc["analysisDate"])
    doc["procedureDate"] = _to_dt(doc["procedureDate"])
    doc["studiesCount"] = _to_int(doc["studiesCount"])
    doc["studySize"] = _to_int(doc["studySize"])
    doc["errorReportSize"] = _to_int(doc["errorReportSize"])
    doc["numberOfMapsCreated"] = _to_int(doc["numberOfMapsCreated"])
    doc["totalPointsCollected"] = _to_int(doc["totalPointsCollected"])
    doc["numberOfAblationSessions"] = _to_int(doc["numberOfAblationSessions"])
    doc["totalAblationTime"] = _to_float(doc["totalAblationTime"])

    return doc
