$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$refs=Join-Path $root 'Excel参考图'
New-Item -ItemType Directory -Path $refs -Force | Out-Null
$excel=New-Object -ComObject Excel.Application
$excel.Visible=$false
$excel.DisplayAlerts=$false
$excel.AutomationSecurity=3
$book=$null
try {
 $book=$excel.Workbooks.Open((Join-Path (Split-Path -Parent $root) '第三章 动态图表.xlsm'),0,$true)
 foreach($sheet in $book.Worksheets){
  if($sheet.ChartObjects().Count -eq 0){continue}
  $chart=$sheet.ChartObjects().Item(1)
  $name=($sheet.Name -replace '[\\/:*?"<>|]','_')
  $path=Join-Path $refs ($name+'.png')
  [void]$chart.Chart.Export($path,'PNG')
  [pscustomobject]@{Sheet=$sheet.Name;Width=$chart.Width;Height=$chart.Height;Left=$chart.Left;Top=$chart.Top} | ConvertTo-Json -Compress
 }
} finally {if($book){$book.Close($false)}; $excel.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
