$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$refs=Join-Path $root 'Excel参考图'
New-Item -ItemType Directory -Path $refs -Force | Out-Null
$excel=New-Object -ComObject Excel.Application
$excel.Visible=$false
$excel.DisplayAlerts=$false
$excel.AutomationSecurity=3
$all=@()
try {
  foreach($file in @('第四章 人力资源可视化看板.xlsx','第四章 销售看板参考.xlsx')) {
    $book=$null
    try {
      $book=$excel.Workbooks.Open((Join-Path (Split-Path -Parent $root) $file),0,$true)
      foreach($sheet in $book.Worksheets) {
        $shapes=@()
        foreach($shape in $sheet.Shapes) {
          $label=''
          try {$label=$shape.TextFrame2.TextRange.Text} catch {}
          $shapes+=@{Name=$shape.Name;Type=$shape.Type;Left=$shape.Left;Top=$shape.Top;Width=$shape.Width;Height=$shape.Height;Text=$label}
        }
        $all+=@{File=$file;Sheet=$sheet.Name;Shapes=$shapes;PrintArea=$sheet.PageSetup.PrintArea}
        $index=0
        foreach($chart in $sheet.ChartObjects()) {
          $index++
          $prefix=if($file -like '*人力*'){'HR'}else{'Sales'}
          [void]$chart.Chart.Export((Join-Path $refs ($prefix+'_'+$sheet.Name+'_'+$index+'.png')),'PNG')
        }
      }
    } finally {if($book){$book.Close($false)}}
  }
} finally {$excel.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
$all | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'Excel对象检查.json') -Encoding utf8
$all | ConvertTo-Json -Depth 8
