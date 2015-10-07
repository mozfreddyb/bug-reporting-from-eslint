from apikey import API_KEY
import requests
import json

DEBUG=True

blocker = 1153855 if DEBUG else 1211384
APIKEY= "LSYNkaRzQHRF6lFzwomA1J7DUzojjQKmxUzLJlSg" if DEBUG else API_KEY
URL= "https://bugzilla-dev.allizom.org/rest/" if DEBUG else \
    "https://bugzilla.mozilla.org/rest/"



components = json.load(file("components.json"))

def get_component(path):
    pp = path.replace("/home/freddy/mozilla/build/gaia/","")
    p = pp.split("/")
    result = (None, None)
    if p[0] == "tv_apps":
        result = (2172, "gaia::tv") # 2172
        if 'system' in p[1]:
            result = (2175, "gaia::tv::system")  # 2175
        elif "home" in p[1]:
            result = (2173, "gaia::tv::home") # 2173,
    elif p[0] == "shared":
        result = (2131, "gaia::shared")
    elif p[1] == "ftu":
        result = (1615, "gaia::first time experience")
    elif p[1] == "email":
        result = (1557, "gaia::e-mail")
    elif p[1] == "costcontrol":
        result = (1604, "gaia::cost control")
    elif p[1] == "emergency-call":
        result = (1605, "gaia::dialer")
    elif p[1] == "communications" and p[2] == "contacts":
        result = (1603, "gaia::contacts")
    elif p[0] == "apps":
        app = p[1]
        for c in components:
            if app in c:
                #print "found", app, c
                result = (components[c], c)
                break
        #elif app == ""
    elif p[0] == "distros" and p[1] == "spark":
        app = p[3]
        for c in components:
            if app in c:
                result = (components[c], c)
                break
    if p[0] == "distros" and p[1] == "spark" and p[3] == "directory":
        result = (2225, "gaia::hackerplace")
    if p[0] == "distros" and p[1] == "spark" and p[3] == "customizer-launcher":
        result = (2223, "gaia::customizer")
    if result[0] == None:
        raise Exception("couldnt find component for path", pp)
    return result


results = json.load(file("innerhtml.json","r"))


bugreports = {}



for item in results:
    if len(item['messages']) < 0:
        continue
    for violation in item['messages']:
        if not violation['message'].startswith("Unsafe"):
            continue
        if 'bower_components' in item["filePath"] or 'b2g_sdk' in item[
            'filePath'] or "node_modules" in item["filePath"] or \
                "build_stage" in item["filePath"] or "dev_apps" in item[
            "filePath"] or 'gaia/tools/' in item["filePath"] or 'gaia/tests' \
                in item["filePath"] or "gaia/build" in item["filePath"] or \
                "sharedtest" in item["filePath"] or "mozspeechcollect" in \
                item["filePath"] or "studio" in item["filePath"] or \
                "privacy-panel" in item["filePath"] or "gaia-component" in \
                item["filePath"]:
            """print
            print "XXX File separate bug for "
            print item
            print"""
            continue


        vmsg =  violation['message']
        component_id, component_name = get_component(item["filePath"])


        nicepath = item["filePath"].replace(
            "/home/freddy/mozilla/build/gaia/","").replace("tv_apps/","")
        title = "{} in {}".format(vmsg, nicepath)


        description = """{}, line {}, column {}:
> {}""".format(title, violation['line'], violation['column'], violation[
                'source'].strip())

        title = 'Unsafe innerHTML/outerHTML/insertAdjacentHTML ' \
                'usage in {}'.format(component_name)


        if component_name in bugreports:
            if vmsg in bugreports[component_name]['findings']:
                bugreports[component_name]['findings'][vmsg].append(
                    [nicepath, violation['line'], violation['column'],
                        violation['source'].strip()])
            else:
                bugreports[component_name]['findings'][vmsg] = [
                    [nicepath, violation['line'], violation['column'],
                     violation['source'].strip()]
                ]

        else:

            bugreports[component_name] = {
                "title": title,
                "findings": {vmsg: [[nicepath, violation['line'], violation[
                    'column'], violation[
                    'source'].strip()]]}
                    # path, line, col, source
            }


        #print "\nDescription:", description



whoamiurl = URL+"whoami?api_key="+API_KEY
res = requests.get(whoamiurl)
import pdb; pdb.set_trace()


URL += "bug?api_key="+API_KEY

for id in bugreports:
    bugentry = bugreports[id]
    description = ""
    for ftype in bugentry['findings']:
        description += ftype+":\n"
        for bug in bugentry['findings'][ftype]:
            if len(bug[3]) < 100:
                description += """In {}, line {}, column {}:
> {}\n""".format(bug[0], bug[1], bug[2], bug[3])
            else:
                description += """In {}, line {}, column {}:
> {}\n""".format(bug[0], bug[1], bug[2], "(code snippet omitted for brevity)")
        description += "\n"
    #print "Title: {}\n".format(bugentry["title"])
    #print description

    ## report:
    params = {
                 "product" : "Firefox OS",
                 "component" : id,
                 "summary" : title,
                 "description": description,
                 "blocks" :{
                     "set": [blocker]
                 },
                 "keywords": {
                     "set": ["sec-want", "wsec-xss"]
                 },
#                 "api_key": API_KEY
             }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    print URL
    res = requests.post(URL, json=params, headers=headers)
    print json.dumps(params, sort_keys=True, indent=4, separators=(',', ': '))

    print res


