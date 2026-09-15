import urllib.request, urllib.parse, urllib.error, http.cookiejar
import base64,json,os,pathlib,secrets,string,time,sys,xml.sax.saxutils,subprocess
root=pathlib.Path(os.environ.get('JENKINS_VALIDATION_ROOT','/lzcsys/var/jenkins-custom'))
base=os.environ.get('JENKINS_VALIDATION_BASE_URL','http://127.0.0.1:18080').rstrip('/')
initial_password=os.environ.get('JENKINS_VALIDATION_INITIAL_PASSWORD','peter111')
plugins_file=pathlib.Path(os.environ.get('JENKINS_VALIDATION_PLUGINS_FILE',str(root/'build/plugins.txt')))
reports_dir=pathlib.Path(os.environ.get('JENKINS_VALIDATION_REPORTS_DIR',str(root/'reports')))
reports_dir.mkdir(parents=True,exist_ok=True)
deadline=time.time()+300
while True:
    try:
        if '--after-restart' in sys.argv:
            password=(root/'secrets/changed-admin-password').read_text().strip()
        else:
            password=initial_password
        if urllib.request.urlopen(base+'/login',timeout=5).status==200: break
    except (OSError,urllib.error.URLError): pass
    if time.time()>deadline: raise SystemExit('Jenkins startup timed out')
    time.sleep(3)
if '--after-restart' in sys.argv:
    assert len(password)==16 and '_' in password
    assert any(c.islower() for c in password) and any(c.isupper() for c in password) and any(c.isdigit() for c in password)
else:
    assert password==initial_password
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
auth='Basic '+base64.b64encode(('admin:'+password).encode()).decode()
def request(path, data=None, ctype=None, crumb=None):
    headers={'Authorization':auth}
    if ctype: headers['Content-Type']=ctype
    if crumb: headers[crumb['crumbRequestField']]=crumb['crumb']
    return opener.open(urllib.request.Request(base+path,data=data,headers=headers),timeout=60).read()
who=json.loads(request('/whoAmI/api/json'))
assert who['authenticated'] and who['name']=='admin'
try:
    urllib.request.urlopen(base+'/api/json',timeout=10)
    raise AssertionError('Anonymous API unexpectedly allowed')
except urllib.error.HTTPError as e: assert e.code in (401,403)
crumb=json.loads(request('/crumbIssuer/api/json'))
script='''import jenkins.model.Jenkins
import groovy.json.JsonOutput
def j=Jenkins.get()
def theme=j.getDescriptor('io.jenkins.plugins.thememanager.ThemeManagerPageDecorator')
println JsonOutput.toJson([theme:theme?.getThemeKey(),executors:j.numExecutors,securityRealm:j.securityRealm.class.name,authorization:j.authorizationStrategy.class.name,failedPlugins:j.pluginManager.failedPlugins.collect{it.name}])
'''
config=json.loads(request('/scriptText',urllib.parse.urlencode({'script':script}).encode(),'application/x-www-form-urlencoded',crumb))
assert config['theme']=='dark',config
assert config['executors']==2
assert not config['failedPlugins'],config
plugins=json.loads(request('/pluginManager/api/json?tree=plugins[shortName,version,active]'))['plugins']
expected=plugins_file.read_text().splitlines()
for name in expected:
    assert any(p['shortName']==name and p['active'] for p in plugins),name
if '--after-restart' in sys.argv:
    result=json.loads(request('/job/toolchain-validation/lastBuild/api/json'))
    assert result['result']=='SUCCESS'
    assert request('/job/toolchain-validation/lastSuccessfulBuild/artifact/toolchain-report.txt')
    initial_auth='Basic '+base64.b64encode(b'admin:peter111').decode()
    initial_req=urllib.request.Request(base+'/whoAmI/api/json',headers={'Authorization':initial_auth})
    try:
        initial_who=json.loads(urllib.request.urlopen(initial_req,timeout=10).read())
        assert not initial_who['authenticated'],initial_who
    except urllib.error.HTTPError as e:
        assert e.code in (401,403)
    print('PASS: changed admin password survives restart, initial password is rejected, theme, plugins, job and artifact persist')
else:
    pipeline="""pipeline {
      agent any
      stages {
        stage('Toolchain smoke test') {
          steps {
            sh '''set -eu
python3.12 -c 'import sys, ssl, sqlite3, bz2, lzma, ctypes; assert sys.version_info[:2] == (3,12)'
python3.12 -m venv .venv
.venv/bin/python -m pip --version
git init -q test-repo
git -C test-repo -c user.name=Validation -c user.email=validation@localhost commit --allow-empty -qm validation
printf 'package main\\nimport "fmt"\\nfunc main(){fmt.Println("go-toolchain-ok")}\\n' > hello.go
GOTOOLCHAIN=local go run hello.go
mkdir -p node-test
cd node-test
npm init -y >/dev/null
node -e 'require("fs").writeFileSync("test.js", "console.log(6*7)")'
npm pkg set scripts.test="node test.js"
npm test
cd ..
{ python3.12 --version; git --version; go version; node --version; npm --version; } > toolchain-report.txt
'''
            archiveArtifacts artifacts: 'toolchain-report.txt', fingerprint: true
          }
        }
      }
    }"""
    xml='<flow-definition plugin="workflow-job"><description>Temporary isolated image verification</description><keepDependencies>false</keepDependencies><properties/><definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps"><script>'+xml.sax.saxutils.escape(pipeline)+'</script><sandbox>true</sandbox></definition><triggers/><disabled>false</disabled></flow-definition>'
    try:
        job=json.loads(request('/job/toolchain-validation/api/json'))
        previous=job['lastBuild']['number'] if job.get('lastBuild') else 0
        request('/job/toolchain-validation/config.xml',xml.encode(),'application/xml',crumb)
    except urllib.error.HTTPError as e:
        if e.code!=404: raise
        previous=0
        request('/createItem?name=toolchain-validation',xml.encode(),'application/xml',crumb)
    request('/job/toolchain-validation/build',b'','application/x-www-form-urlencoded',crumb)
    deadline=time.time()+300
    while True:
        try:
            result=json.loads(request('/job/toolchain-validation/lastBuild/api/json'))
            if result['number']>previous and not result['building']:
                (reports_dir/'pipeline-console.txt').write_bytes(request('/job/toolchain-validation/lastBuild/consoleText'))
                assert result['result']=='SUCCESS',result['result']
                break
        except urllib.error.HTTPError as e:
            if e.code!=404: raise
        if time.time()>deadline: raise SystemExit('Pipeline timed out')
        time.sleep(3)
    (reports_dir/'toolchain-report.txt').write_bytes(request('/job/toolchain-validation/lastSuccessfulBuild/artifact/toolchain-report.txt'))
    (reports_dir/'plugins.lock.json').write_text(json.dumps(sorted(plugins,key=lambda p:p['shortName']),indent=2)+'\n')
    (reports_dir/'jenkins-config-check.json').write_text(json.dumps(config,indent=2)+'\n')
    alphabet=string.ascii_letters+string.digits+'_'
    while True:
        changed=''.join(secrets.choice(alphabet) for _ in range(16))
        if all(any(c in group for c in changed) for group in [string.ascii_lowercase,string.ascii_uppercase,string.digits,'_']): break
    change_script='''import hudson.model.User
import hudson.security.HudsonPrivateSecurityRealm
def u=User.getById("admin", false)
u.addProperty(HudsonPrivateSecurityRealm.Details.fromPlainPassword(%s))
u.save()
println "password-updated"
''' % json.dumps(changed)
    response=request('/scriptText',urllib.parse.urlencode({'script':change_script}).encode(),'application/x-www-form-urlencoded',crumb).decode()
    assert 'password-updated' in response,response
    changed_file=root/'secrets/changed-admin-password'
    changed_file.write_text(changed+'\n')
    changed_file.chmod(0o600)
    print('PASS: initial admin login, anonymous access denied, dark theme, plugins, pipeline, artifacts, password change')
    print((reports_dir/'toolchain-report.txt').read_text())
