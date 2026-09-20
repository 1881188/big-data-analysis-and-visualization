$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$refs=Join-Path $root 'Excel参考图'
$excel=New-Object -ComObject Excel.Application
$excel.Visible=$false
$excel.DisplayAlerts=$false
$excel.AutomationSecurity=3
try {
 foreach($kind in @('HR','Sales')) {
  $file=if($kind -eq 'HR'){'第四章 人力资源可视化看板.xlsx'}else{'第四章 销售看板参考.xlsx'}
  $book=$null
  try {
   $book=$excel.Workbooks.Open((Join-Path (Split-Path -Parent $root) $file),0,$true)
   $sheet=if($kind -eq 'HR'){$book.Worksheets.Item(1)}else{$book.Worksheets.Item('数据大屏')}
   $sheet.Activate()
   $i=0
   foreach($chart in $sheet.ChartObjects()) {
    $i++
    $chart.Activate()
    $chart.Chart.Refresh()
    $ok=$chart.Chart.Export((Join-Path $refs ($kind+'_'+$sheet.Name+'_'+$i+'.png')),'PNG')
    Write-Output "$kind chart $i : $ok"
   }
   if($kind -eq 'HR'){$range=$sheet.Range('P1:Z25')}else{$range=$sheet.Range('E1:W40')}
   Write-Output ($kind+' left '+$range.Left+' top '+$range.Top+' width '+$range.Width+' height '+$range.Height)
   $range.CopyPicture(1,2)
   $temp=$excel.Workbooks.Add()
   try {
    $target=$temp.Worksheets.Item(1).ChartObjects().Add(0,0,$range.Width,$range.Height)
    $target.Activate()
    $target.Chart.Paste()
    [void]$target.Chart.Export((Join-Path $refs ($kind+'_整屏.png')),'PNG')
   } finally {$temp.Close($false)}
  } finally {if($book){$book.Close($false)}}
 }
} finally {$excel.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
