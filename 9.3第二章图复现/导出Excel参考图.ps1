$ErrorActionPreference = 'Stop'

$targetDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$referenceDirectory = Join-Path $targetDirectory 'Excel参考原图'
New-Item -ItemType Directory -Path $referenceDirectory -Force | Out-Null

$workbooks = @(
    (Join-Path $targetDirectory '第二章 图表(前15).xlsx'),
    (Join-Path $targetDirectory '第二章 图表(后15).xlsx')
)

function Get-SafeName([string]$name) {
    return ($name.Trim() -replace '[\\/:*?"<>|]', '_')
}

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$excel.ScreenUpdating = $false
$sequence = 1

try {
    foreach ($workbookPath in $workbooks) {
        $workbook = $excel.Workbooks.Open($workbookPath, 0, $true)
        try {
            foreach ($worksheet in $workbook.Worksheets) {
                $safeName = Get-SafeName $worksheet.Name
                $outputPath = Join-Path $referenceDirectory ('{0:D2}_{1}_Excel原图.png' -f $sequence, $safeName)
                $chartObjects = $worksheet.ChartObjects()

                if ($chartObjects.Count -gt 0) {
                    $selected = $null
                    $largestArea = -1
                    for ($index = 1; $index -le $chartObjects.Count; $index++) {
                        $candidate = $chartObjects.Item($index)
                        $area = [double]$candidate.Width * [double]$candidate.Height
                        if ($area -gt $largestArea) {
                            if ($null -ne $selected) {
                                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($selected)
                            }
                            $selected = $candidate
                            $largestArea = $area
                        }
                        else {
                            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidate)
                        }
                    }
                    $exported = $selected.Chart.Export($outputPath, 'PNG')
                    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($selected)
                }
                else {
                    # 第 7 图没有 ChartObject，使用工作表已用区域的图片副本。
                    $usedRange = $worksheet.UsedRange
                    $usedRange.CopyPicture(1, 2)
                    $temporary = $worksheet.ChartObjects().Add(
                        $usedRange.Left,
                        $usedRange.Top,
                        $usedRange.Width,
                        $usedRange.Height
                    )
                    $temporary.Chart.Paste() | Out-Null
                    $exported = $temporary.Chart.Export($outputPath, 'PNG')
                    $temporary.Delete()
                    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($temporary)
                    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($usedRange)
                }

                if (-not $exported) {
                    throw "导出失败：$($worksheet.Name)"
                }
                Write-Output ('{0:D2} {1}' -f $sequence, $outputPath)
                $sequence++
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($chartObjects)
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet)
            }
        }
        finally {
            $workbook.Close($false)
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook)
        }
    }
}
finally {
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
