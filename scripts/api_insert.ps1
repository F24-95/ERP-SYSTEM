# School ERP - API Data Inserter
# Inserts 5 records per table via POST/PUT API endpoints
$baseUrl = "http://127.0.0.1:8000"
$ErrorActionPreference = "Continue"

# ── Login ────────────────────────────────────────────────────────────
function Get-Token($email, $password) {
    $body = @{email=$email; password=$password} | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
        return $r.access_token
    } catch { return $null }
}

$adminToken = Get-Token "admin1@school.com" "password@123"
$teacherToken = Get-Token "teacher1@school.com" "password@123"
$studentToken = Get-Token "student1@school.com" "password@123"

if (-not $adminToken) { Write-Error "Admin login failed!"; exit 1 }

$adminHeaders = @{Authorization = "Bearer $adminToken"}
$teacherHeaders = @{Authorization = "Bearer $teacherToken"}
$studentHeaders = @{Authorization = "Bearer $studentToken"}

Write-Output "=== Logged in as admin/teacher/student ==="

# ── Helper to POST JSON ──────────────────────────────────────────────
function Post-Json($url, $body, $headers) {
    try {
        $b = $body | ConvertTo-Json -Depth 10
        $r = Invoke-RestMethod -Uri "$baseUrl$url" -Method Post -Body $b -ContentType "application/json" -Headers $headers -TimeoutSec 15
        Write-Output "  [OK] POST $url"
        return $r
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        $detail = ""
        try { $detail = ($_.ErrorDetails.Message | ConvertFrom-Json).detail } catch { $detail = $_.Exception.Message.Substring(0, [Math]::Min(100, $_.Exception.Message.Length)) }
        Write-Output "  [SKIP] POST $url -> $status ($detail)"
        return $null
    }
}

function Put-Json($url, $body, $headers) {
    try {
        $b = $body | ConvertTo-Json -Depth 10
        $r = Invoke-RestMethod -Uri "$baseUrl$url" -Method Put -Body $b -ContentType "application/json" -Headers $headers -TimeoutSec 15
        Write-Output "  [OK] PUT $url"
        return $r
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        Write-Output "  [SKIP] PUT $url -> $status"
        return $null
    }
}

# ── 1. ACADEMIC SESSIONS (5 new) ──────────────────────────────────
Write-Output "`n=== 1. Academic Sessions ==="
$sessionCodes = @("SES-2728", "SES-2829", "SES-2930", "SES-3031", "SES-3132")
$sessionNames = @("2027-28", "2028-29", "2029-30", "2030-31", "2031-32")
$sYears = 2027..2031
$eYears = 2028..2032
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/academics/sessions" @{
        session_code = $sessionCodes[$i]; session_name = $sessionNames[$i]
        start_year = $sYears[$i]; end_year = $eYears[$i]
        start_date = "2027-04-01"; end_date = "2028-03-31"
    } $adminHeaders
}
Start-Sleep 1

# ── Get reference IDs ──────────────────────────────────────────────
$env:PGPASSWORD="Faizan9517"
$psql = '"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -U postgres -d faizan20 -t -A'

# Users
$adminIds = @(1,2); $teacherUserIds = @(3,4,5,6); $studentUserIds = @(7,8,9,10,11,12,13,14,15,16,17,18,19,20); $parentIds = @(21,22,23,24,25)
$sessions = @((& cmd /c "$psql -c ""SELECT id FROM academic_sessions ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""})
$sessId = [int]$sessions[-1]
$sessId1 = [int]$sessions[0]; $sessId2 = [int]$sessions[1]; $sessId3 = [int]$sessions[2]
$classIds = @(1..8); $subjIds = @(1..12)
$csIds = @(1..96)
$wdIds = @(1..7); $tsIds = @(1..8)
$teacherProfIds = @(1..4); $studentProfIds = @(1..14)

Write-Output "  Reference: session=$sessId, class=1..8, subject=1..12"

# ── 2. CLASSROOMS (5 new) ─────────────────────────────────────────
Write-Output "`n=== 2. Classrooms ==="
$classCodes = @("CLS-10A","CLS-10B","CLS-11A","CLS-11B","CLS-12A")
$classNames = @("Class 10","Class 10","Class 11","Class 11","Class 12")
$sections = @("A","B","A","B","A")
$displayNames = @("X-A","X-B","XI-A","XI-B","XII-A")
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/academics/classrooms" @{
        class_code = $classCodes[$i]; class_name = $classNames[$i]; section = $sections[$i]
        display_name = $displayNames[$i]; academic_sessions_id = $sessId
    } $adminHeaders
}

# ── 3. SUBJECTS (5 new) ──────────────────────────────────────────
Write-Output "`n=== 3. Subjects ==="
$subjCodes = @("BIO01","CHE01","PHY01","ECO01","HIS01")
$subjNames = @("Biology","Chemistry","Physics","Economics","History")
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/academics/subjects" @{
        subject_code = $subjCodes[$i]; subject_name = $subjNames[$i]; subject_type = "Core"; display_order = 20+$i
    } $adminHeaders
}

# ── 4. CLASS-SUBJECTS (5 new) ───────────────────────────────────
Write-Output "`n=== 4. Class Subjects ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/academics/class-subjects" @{
        academic_sessions_id = $sessId; classroom_id = $classIds[0]; subject_id = $subjIds[$i]; display_order = 100+$i
    } $adminHeaders
}

# ── 5. CREATE NEW USERS via admin ─────────────────────────────────
Write-Output "`n=== 5. New Users (via POST /admin/user) ==="
for ($i = 0; $i -lt 2; $i++) {
    $idx = 30 + $i
    Post-Json "/admin/user" @{
        email = "newadmin$idx@school.com"; phone = "9876543$idx"; role = "admin"; password = "password@123"
    } $adminHeaders
}
for ($i = 0; $i -lt 2; $i++) {
    $idx = 40 + $i
    Post-Json "/admin/user" @{
        email = "newteacher$idx@school.com"; phone = "9876543$idx"; role = "teacher"; password = "password@123"
    } $adminHeaders
}
for ($i = 0; $i -lt 5; $i++) {
    $idx = 50 + $i
    Post-Json "/admin/user" @{
        email = "newstudent$idx@school.com"; phone = "9876543$idx"; role = "student"; password = "password@123"
    } $adminHeaders
}

# Refresh user IDs
$allUsers = @((& cmd /c "$psql -c ""SELECT id FROM users WHERE role='ADMIN' ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
$allTeachers = @((& cmd /c "$psql -c ""SELECT id FROM users WHERE role='TEACHER' ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
$allStudents = @((& cmd /c "$psql -c ""SELECT id FROM users WHERE role='STUDENT' ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
Write-Output "  Users refreshed: admins=$($allUsers.Count), teachers=$($allTeachers.Count), students=$($allStudents.Count)"

# ── 6. WEEK DAYS ─────────────────────────────────────────────────
Write-Output "`n=== 6. Week Days ==="
# Week days normally only have 7, skip if full
Post-Json "/weekdays" @{day_code="WKD"; day_name="WeeklyDay"; display_order=8} $adminHeaders

# ── 7. TIME SLOTS (5 new) ───────────────────────────────────────
Write-Output "`n=== 7. Time Slots ==="
for ($i = 0; $i -lt 5; $i++) {
    $h = 13 + $i
    Post-Json "/timeslots" @{
        slot_code = "SLOT$($h+10)"; slot_name = "Extra Period $($i+1)"
        start_time = "$h`:$([string](30*$i%60)):00"; end_time = "$($h+1):$(30*$i%60):00"
        duration_minutes = 45; display_order = 20+$i; is_break = $false
    } $adminHeaders
}

# Refresh time slot IDs
$tsIds = @((& cmd /c "$psql -c ""SELECT id FROM time_slots ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
$wdIds = @((& cmd /c "$psql -c ""SELECT id FROM week_days ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})

# ── 8. TEACHER SUBJECTS (assign 5) ────────────────────────────────
Write-Output "`n=== 8. Teacher Subjects (assign) ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/operations/assign-teacher" @{
        academic_sessions_id = $sessId; class_subject_id = $csIds[$i % $csIds.Count]
        classroom_id = $classIds[$i % $classIds.Count]; subject_id = $subjIds[$i % $subjIds.Count]
        teacher_id = $allTeachers[$i % $allTeachers.Count]; is_class_teacher = ($i -eq 0)
    } $adminHeaders
}

# ── 9. ENROLL STUDENTS (5 new) ──────────────────────────────────
Write-Output "`n=== 9. Enroll Students ==="
# First new students need profiles (no POST endpoint for profiles, skip this)
# Just enroll existing students who may not have enrollments
for ($i = 0; $i -lt [Math]::Min(5, $allStudents.Count); $i++) {
    Post-Json "/operations/enroll-student" @{
        academic_sessions_id = $sessId; student_id = $allStudents[$i]; classroom_id = $classIds[$i % $classIds.Count]
        roll_number = (50 + $i); admission_date = "2027-06-01"
    } $adminHeaders
}

# ── 10. TIMETABLE (5 entries) ─────────────────────────────────────
Write-Output "`n=== 10. Timetable ==="
$tsTeachRows = @((& cmd /c "$psql -c ""SELECT id FROM teacher_subjects ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/timetable" @{
        timetable_id = "TT$(100000+$i+1)"; academic_sessions_id = $sessId; classroom_id = $classIds[$i % $classIds.Count]
        class_subject_id = $csIds[$i % $csIds.Count]; teacher_subject_id = $tsTeachRows[$i % $tsTeachRows.Count]
        week_day_id = $wdIds[$i % $wdIds.Count]; time_slot_id = $tsIds[$i % $tsIds.Count]; room_number = "Room $(300+$i)"
    } $adminHeaders
}

# ── 11. TEACHER AVAILABILITY (5) ──────────────────────────────
Write-Output "`n=== 11. Teacher Availability ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/availability" @{
        availability_id = "TA$(10000+$i+1)"; academic_sessions_id = $sessId
        teacher_subject_id = $tsTeachRows[$i % $tsTeachRows.Count]; week_day_id = $wdIds[$i % $wdIds.Count]
        time_slot_id = $tsIds[$i % $tsIds.Count]; is_available = $true
    } $teacherHeaders
}

# ── 12. DAILY CLASSES (5) ──────────────────────────────────────
Write-Output "`n=== 12. Daily Classes ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/daily-class/" @{
        daily_class_id = "DCL$(1000+$i+1)"; academic_sessions_id = $sessId
        classroom_id = $classIds[$i % $classIds.Count]; class_subject_id = $csIds[$i % $csIds.Count]
        teacher_subject_id = $tsTeachRows[$i % $tsTeachRows.Count]
        class_date = "2026-07-2$i"; topic = "API Class $i"
    } $teacherHeaders
}

# ── 13. FEES (5) ──────────────────────────────────────────────────
Write-Output "`n=== 13. Fees ==="
$stuClassRows = @((& cmd /c "$psql -c ""SELECT id FROM student_classes ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/fees" @{
        academic_sessions_id = $sessId; student_class_id = $stuClassRows[$i % $stuClassRows.Count]
        fee_month = (8 + $i); fee_year = 2027; total_amount = (2500 + $i * 100); due_date = "2027-08-15"
    } $adminHeaders
}

# ── 14. EXAMS (5) ─────────────────────────────────────────────────
Write-Output "`n=== 14. Exams ==="
$examIds = @()
for ($i = 0; $i -lt 5; $i++) {
    $eid = "EXM$(90000000+$i+1)"
    $r = Post-Json "/exams/" @{
        exam_id = $eid; academic_sessions_id = $sessId; classroom_id = $classIds[$i % $classIds.Count]
        class_subject_id = $csIds[$i % $csIds.Count]; teacher_subject_id = $tsTeachRows[$i % $tsTeachRows.Count]
        exam_name = "API Test $($i+1)"; exam_type = "Theory"; exam_date = "2026-09-1$i"
        total_marks = 50; passing_marks = 20
    } $teacherHeaders
    if ($r) { $examIds += $r.id }
}
# Fallback: get exam IDs from DB
if ($examIds.Count -eq 0) {
    $examIds = @((& cmd /c "$psql -c ""SELECT id FROM exams ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
}

# ── 15. EXAM RESULTS (5) ──────────────────────────────────────────
Write-Output "`n=== 15. Exam Results ==="
foreach ($eid in $examIds[0..[Math]::Min(4, $examIds.Count-1)]) {
    $results = @()
    for ($j = 0; $j -lt [Math]::Min(3, $stuClassRows.Count); $j++) {
        $results += @{student_class_id = $stuClassRows[$j]; obtained_marks = (30 + $j * 5); percentage = (60 + $j * 10); grade = "A"}
    }
    if ($results.Count -gt 0) {
        try {
            $b = $results | ConvertTo-Json -Depth 10
            Invoke-RestMethod -Uri "$baseUrl/exams/$eid/results" -Method Post -Body $b -ContentType "application/json" -Headers $teacherHeaders -TimeoutSec 15 | Out-Null
            Write-Output "  [OK] POST /exams/$eid/results"
        } catch { Write-Output "  [SKIP] POST /exams/$eid/results" }
    }
}

# ── 16. ASSIGNMENTS (5) ──────────────────────────────────────────
Write-Output "`n=== 16. Assignments ==="
$asnIds = @()
for ($i = 0; $i -lt 5; $i++) {
    $aid = "ASN$(90000000+$i+1)"
    $r = Post-Json "/assignments/" @{
        assignment_id = $aid; academic_sessions_id = $sessId; classroom_id = $classIds[$i % $classIds.Count]
        class_subject_id = $csIds[$i % $csIds.Count]; teacher_subject_id = $tsTeachRows[$i % $tsTeachRows.Count]
        title = "API Assignment $($i+1)"; due_date = "2026-09-2$i"; total_marks = 20; passing_marks = 10
    } $teacherHeaders
    if ($r) { $asnIds += $r.id }
}
if ($asnIds.Count -eq 0) {
    $asnIds = @((& cmd /c "$psql -c ""SELECT id FROM assignments ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
}

# ── 17. ASSIGNMENT RESULTS (5) ──────────────────────────────────
Write-Output "`n=== 17. Assignment Results ==="
foreach ($aid in $asnIds[0..[Math]::Min(4, $asnIds.Count-1)]) {
    $results = @()
    for ($j = 0; $j -lt [Math]::Min(3, $stuClassRows.Count); $j++) {
        $results += @{student_class_id = $stuClassRows[$j]; obtained_marks = (15 + $j * 2); percentage = (75 + $j * 5); grade = "A"}
    }
    if ($results.Count -gt 0) {
        try {
            $b = $results | ConvertTo-Json -Depth 10
            Invoke-RestMethod -Uri "$baseUrl/assignments/$aid/results" -Method Post -Body $b -ContentType "application/json" -Headers $teacherHeaders -TimeoutSec 15 | Out-Null
            Write-Output "  [OK] POST /assignments/$aid/results"
        } catch { Write-Output "  [SKIP] POST /assignments/$aid/results" }
    }
}

# ── 18. STUDY MATERIALS (5 - multipart) ──────────────────────────
Write-Output "`n=== 18. Study Materials ==="
for ($i = 0; $i -lt 5; $i++) {
    $url = "$baseUrl/study-materials"
    $boundary = [guid]::NewGuid().ToString()
    $bodyLines = @()
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"title`""
    $bodyLines += ""
    $bodyLines += "API Material $($i+1)"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"academic_sessions_id`""
    $bodyLines += ""
    $bodyLines += "$sessId"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"classroom_id`""
    $bodyLines += ""
    $bodyLines += "$($classIds[$i % $classIds.Count])"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"class_subject_id`""
    $bodyLines += ""
    $bodyLines += "$($csIds[$i % $csIds.Count])"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"teacher_subject_id`""
    $bodyLines += ""
    $bodyLines += "$($tsTeachRows[$i % $tsTeachRows.Count])"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"file`"; filename=`"test$i.txt`""
    $bodyLines += "Content-Type: text/plain"
    $bodyLines += ""
    $bodyLines += "API test content $i"
    $bodyLines += "--$boundary--"
    $bodyStr = [string]::Join("`r`n", $bodyLines)
    try {
        Invoke-RestMethod -Uri $url -Method Post -Body $bodyStr -ContentType "multipart/form-data; boundary=$boundary" -Headers $adminHeaders -TimeoutSec 15 | Out-Null
        Write-Output "  [OK] POST /study-materials #$i"
    } catch { Write-Output "  [SKIP] POST /study-materials #$i" }
}

# ── 19. NOTICES (5 - multipart) ──────────────────────────────────
Write-Output "`n=== 19. Notices ==="
for ($i = 0; $i -lt 5; $i++) {
    $url = "$baseUrl/notices/"
    $boundary = [guid]::NewGuid().ToString()
    $bodyLines = @()
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"title`""
    $bodyLines += ""
    $bodyLines += "API Notice $($i+1)"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"description`""
    $bodyLines += ""
    $bodyLines += "Created via API test - notice $($i+1)"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"notice_type`""
    $bodyLines += ""
    $bodyLines += "GENERAL"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"audience`""
    $bodyLines += ""
    $bodyLines += "ALL"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"publish_date`""
    $bodyLines += ""
    $bodyLines += "2026-07-2$i"
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"academic_sessions_id`""
    $bodyLines += ""
    $bodyLines += "$sessId"
    $bodyLines += "--$boundary--"
    $bodyStr = [string]::Join("`r`n", $bodyLines)
    try {
        Invoke-RestMethod -Uri $url -Method Post -Body $bodyStr -ContentType "multipart/form-data; boundary=$boundary" -Headers $adminHeaders -TimeoutSec 15 | Out-Null
        Write-Output "  [OK] POST /notices/ #$i"
    } catch { Write-Output "  [SKIP] POST /notices/ #$i" }
}

# ── 20. CHAT ROOMS (5) ─────────────────────────────────────────
Write-Output "`n=== 20. Chat Rooms ==="
$crIds = @()
for ($i = 0; $i -lt 5; $i++) {
    $r = Post-Json "/chat/rooms" @{
        chat_room_id = "CHT$(90000000+$i+1)"; academic_sessions_id = $sessId
        student_class_id = $stuClassRows[$i % $stuClassRows.Count]; teacher_subject_id = $tsTeachRows[$i % $tsTeachRows.Count]
    } $teacherHeaders
    if ($r) { $crIds += $r.id }
}
if ($crIds.Count -eq 0) {
    $crIds = @((& cmd /c "$psql -c ""SELECT id FROM chat_rooms ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
}

# ── 21. CHAT MESSAGES (5) ──────────────────────────────────────
Write-Output "`n=== 21. Chat Messages ==="
foreach ($crid in $crIds[0..[Math]::Min(4, $crIds.Count-1)]) {
    Post-Json "/chat/rooms/$crid/messages" @{message = "API test message to room $crid"} $studentHeaders
}

# ── 22. ID CARDS (5) ──────────────────────────────────────────────
Write-Output "`n=== 22. Student ID Cards ==="
$spIds = @((& cmd /c "$psql -c ""SELECT id FROM student_profiles ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
foreach ($spId in $spIds[0..[Math]::Min(4, $spIds.Count-1)]) {
    try {
        Invoke-RestMethod -Uri "$baseUrl/student/id-card/$spId" -Method Post -Headers $adminHeaders -TimeoutSec 15 | Out-Null
        Write-Output "  [OK] POST /student/id-card/$spId"
    } catch { Write-Output "  [SKIP] POST /student/id-card/$spId" }
}

# ── 23. KA TOPICS (5) ──────────────────────────────────────────
Write-Output "`n=== 23. KA Topics ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/khan-academy/topics" @{
        ka_topic_id = "ka_api_$(100+$i)"; topic_name = "API Topic $($i+1)"; subject_id = $subjIds[$i % $subjIds.Count]; display_order = (100+$i)
    } $adminHeaders
}

# ── 24. KA STUDENT ACTIVITIES (5) ──────────────────────────────
Write-Output "`n=== 24. KA Student Activities ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/khan-academy/activity/student" @{
        student_profile_id = $spIds[$i % $spIds.Count]; from_date = "2026-07-01"; to_date = "2026-07-15"
        worked_on = (5+$i); attempted = (3+$i); minutes = (30+$i*10)
    } $adminHeaders
}

# ── 25. KA SUBJECT ACTIVITIES (5) ─────────────────────────────
Write-Output "`n=== 25. KA Subject Activities ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/khan-academy/activity/subject" @{
        student_profile_id = $spIds[$i % $spIds.Count]; subject_id = $subjIds[$i % $subjIds.Count]; activity_date = "2026-07-2$i"
    } $adminHeaders
}

# ── 26. KA SUBJECT PROGRESS (5) ──────────────────────────────
Write-Output "`n=== 26. KA Subject Progress ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/khan-academy/progress/subject" @{
        student_profile_id = $spIds[$i % $spIds.Count]; subject_id = $subjIds[$i % $subjIds.Count]
        point_available = (100+$i*10); point_earned = (50+$i*5); snapshot_date = "2026-07-2$i"
    } $adminHeaders
}

# ── 27. KA TOPIC PROGRESS (5) ────────────────────────────────
Write-Output "`n=== 27. KA Topic Progress ==="
$kaTopics = @((& cmd /c "$psql -c ""SELECT id FROM ka_topics ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/khan-academy/progress/topic" @{
        student_profile_id = $spIds[$i % $spIds.Count]; topic_id = $kaTopics[$i % $kaTopics.Count]
        subject_id = $subjIds[$i % $subjIds.Count]; point_available = 50; point_earned = 25; snapshot_date = "2026-07-2$i"
    } $adminHeaders
}

# ── 28. ATTACHMENTS (5) ─────────────────────────────────────────
Write-Output "`n=== 28. Attachments ==="
for ($i = 0; $i -lt 5; $i++) {
    $base64data = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("API test attachment $i"))
    Post-Json "/attachments/upload" @{
        entity_type = "assignment"; entity_id = 1; file_name = "api_test_$i.txt"; mime_type = "text/plain"; file_data = $base64data
    } $adminHeaders
}

# ── 29. ZOOM MEETINGS (5) ────────────────────────────────────────
Write-Output "`n=== 29. Zoom Meetings ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/zoom/meetings" @{
        uuid = "api-$(New-Guid)"; meeting_id = (90000000000+$i); topic = "API Zoom $($i+1)"; type = 2; duration = 45
    } $adminHeaders
}

# ── 30. ZOOM FILES (5) ──────────────────────────────────────────
Write-Output "`n=== 30. Zoom Files ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/zoom/files" @{
        file_initial = "API_$($i)"; raw_date = "2026-07-2$i"; raw_time = "10:00:00"; date = "2026-07-2$i"; time = "10:00"
    } $adminHeaders
}

# ── 31. STUDENT PROMOTION (5) ──────────────────────────────────
Write-Output "`n=== 31. Student Promotion ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/operations/promote-student" @{
        student_id = $allStudents[$i % $allStudents.Count]; from_session_id = $sessId1; to_session_id = $sessId
        to_classroom_id = $classIds[$i % $classIds.Count]; new_roll = (60+$i)
    } $adminHeaders
}

# ── 32. STUDENT ATTENDANCE recalculate ──────────────────────────
Write-Output "`n=== 32. Student Attendance Recalculate ==="
foreach ($scId in $stuClassRows[0..[Math]::Min(4, $stuClassRows.Count-1)]) {
    try {
        Invoke-RestMethod -Uri "$baseUrl/daily-class/attendance/recalculate/$scId" -Method Post -Headers $teacherHeaders -TimeoutSec 15 | Out-Null
        Write-Output "  [OK] POST /daily-class/attendance/recalculate/$scId"
    } catch { Write-Output "  [SKIP] POST /daily-class/attendance/recalculate/$scId" }
}

# ── 33. REPORTS (5) ──────────────────────────────────────────────
Write-Output "`n=== 33. Reports ==="
for ($i = 0; $i -lt 5; $i++) {
    Post-Json "/reports/generate" @{
        student_profile_id = $spIds[$i % $spIds.Count]; data_start_date = "2026-07-01"; data_end_date = "2026-07-15"
    } $adminHeaders
}

# Get report IDs and add sub-reports
Start-Sleep 1
$repIds = @((& cmd /c "$psql -c ""SELECT id FROM student_reports ORDER BY id"" 2>nul") -split "`n" | Where-Object {$_ -ne ""} | ForEach-Object {[int]$_})
Write-Output "=== 34. Report Sub-entities ==="
foreach ($rid in $repIds[0..[Math]::Min(4, $repIds.Count-1)]) {
    Put-Json "/reports/$rid/activity" @{mean_duration_minutes = 30; total_duration_minutes = 500; total_worked_hours = 10; total_attempted = 25} $adminHeaders
    Put-Json "/reports/$rid/zoom-duration" @{mean_duration_minutes = 25; min_duration_minutes = 10; max_duration_minutes = 45} $adminHeaders
    Put-Json "/reports/$rid/zoom-interaction" @{mean_interaction_count = 8; min_interaction_count = 2; max_interaction_count = 15} $adminHeaders
}

# ── SUMMARY ──────────────────────────────────────────────────────
Write-Output "`n`n============================================="
Write-Output "API Data Insertion Complete!"
Write-Output "============================================="
Write-Output "Getting final counts..."
Start-Sleep 2

$tables = @("users","academic_sessions","classroom","subjects","class_subjects","teacher_subjects","student_classes","week_days","time_slots","class_timetable","teacher_availability","daily_classes","daily_class_students","student_attendance","fees","exams","exam_results","assignments","assignment_results","study_materials","notices","chat_rooms","chat_messages","student_id_cards","ka_topics","ka_student_activities","ka_subject_activities","ka_subject_progress","ka_topic_progress","attachments","zoom_meetings","zoom_files","student_reports","student_activity_reports","student_subject_progress_reports","student_topic_progress_reports","zoom_duration_reports","zoom_interaction_reports","student_promotion_history","otp_codes","revoked_tokens","admin_profiles","teacher_profiles","student_profiles","processed_meetings","processed_participants","raw_meetings","raw_participants","zoom_transcripts","zoom_student_interactions","zoom_participants","zoom_recording_files")

foreach ($t in $tables) {
    $count = & cmd /c "$psql -c ""SELECT COUNT(*) FROM $t"" 2>nul"
    Write-Output "  $t -> $count"
}
