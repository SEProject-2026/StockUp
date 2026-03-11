<#
.SYNOPSIS
    Cleans the background of a scanned text document using ImageMagick.
    Ported from Fred Weinhaus's 'textcleaner' Bash script.

.DESCRIPTION
    TEXTCLEANER processes a scanned document of text to clean the text background 
    and enhance the text.

.PARAMETER InputFile
    The path to the source image.

.PARAMETER OutputFile
    The path where the cleaned image will be saved.

.PARAMETER Rotate
    Rotate image 90 degrees if aspect ratio does not match layout. 
    Options: 'none', 'cw' (clockwise), 'ccw' (counterclockwise). Default: 'none'

.PARAMETER Layout
    Desired layout. Options: 'portrait', 'landscape'. Default: 'portrait'

.PARAMETER CropOffsets
    Image cropping offsets. Comma-separated integers (1, 2, or 4 values).

.PARAMETER Grayscale
    Convert document to grayscale before enhancing. Switch.

.PARAMETER Enhance
    Enhance image brightness. Options: 'none', 'stretch', 'normalize'. Default: 'stretch'

.PARAMETER FilterSize
    Size of filter used to clean background. Integer > 0. Default: 15

.PARAMETER Offset
    Offset of filter in percent to reduce noise. Integer >= 0. Default: 5

.PARAMETER Unrotate
    Unrotate image (deskew). Switch.

.PARAMETER Preserve
    Preserve input size after unrotate. Switch.

.PARAMETER Threshold
    Text smoothing threshold (0-100). Default: $null (no smoothing).

.PARAMETER Sharpen
    Sharpening amount in pixels. Float >= 0. Default: 0

.PARAMETER Saturation
    Color saturation percent. Default: 200.

.PARAMETER AdaptBlur
    Adaptive blur amount. Float >= 0. Default: 0

.PARAMETER Trim
    Trim background around outer part of image. Switch.

.PARAMETER Pad
    Border pad amount. Integer >= 0. Default: 0

.PARAMETER BgColor
    Desired background color. Default: 'white'. Use 'image' to detect from top-left.

.PARAMETER Fuzz
    Fuzz value for determining bgcolor when BgColor='image'. Default: 10.

.PARAMETER Invert
    Invert colors. Options: 0 (none), 1 (input), 2 (input and output). Default: 0.

.PARAMETER Compression
    TIFF compression. Options: 'none', 'lzw', 'zip', 'fax', 'group4'. Default: 'none'

.PARAMETER Density
    Input density for vector files (PDF). Integer > 0.

.PARAMETER Resize
    Resize percentage (0-100). Default: $null (no resize).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$InputFile,

    [Parameter(Mandatory=$true, Position=1)]
    [string]$OutputFile,

    [ValidateSet("none", "cw", "ccw", "n", "clockwise", "counterclockwise")]
    [string]$Rotate = "none",

    [ValidateSet("portrait", "landscape", "p", "l")]
    [string]$Layout = "portrait",

    [string]$CropOffsets = "",

    [switch]$Grayscale,

    [ValidateSet("none", "stretch", "normalize")]
    [string]$Enhance = "stretch",

    [int]$FilterSize = 15,

    [int]$Offset = 5,

    [switch]$Unrotate,

    [switch]$Preserve,

    [int]$Threshold = -1, # Using -1 to represent "not set"

    [double]$Sharpen = 0,

    [int]$Saturation = 200,

    [double]$AdaptBlur = 0,

    [switch]$Trim,

    [int]$Pad = 0,

    [string]$BgColor = "white",

    [int]$Fuzz = 10,

    [ValidateSet(0, 1, 2)]
    [int]$Invert = 0,

    [ValidateSet("none", "lzw", "zip", "fax", "group4", "n", "l", "z", "f", "g")]
    [string]$Compression = "none",

    [int]$Density = 0, # 0 means not set

    [int]$Resize = 0 # 0 means not set
)

# --- Configuration ---
# Set this to 'magick' for ImageMagick v7+, or 'convert' for v6
$IMBinary = "magick"

# --- Helper Functions ---

function Exit-WithError {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

function Get-ImageInfo {
    param($Path, $Format)
    $val = & $IMBinary "$Path" -ping -format "$Format" info:
    return $val
}

# --- Validation and Setup ---

if (-not (Test-Path $InputFile)) {
    Exit-WithError "Input file not found: $InputFile"
}

# Normalize Parameter Strings
$Rotate = $Rotate.ToLower()
if ($Rotate -eq "n") { $Rotate = "none" }
if ($Rotate -eq "clockwise") { $Rotate = "cw" }
if ($Rotate -eq "counterclockwise") { $Rotate = "ccw" }

$Layout = $Layout.ToLower()
if ($Layout -eq "p") { $Layout = "portrait" }
if ($Layout -eq "l") { $Layout = "landscape" }

# Crop Parsing
$NumCrops = 0
$Crop1 = $Crop2 = $Crop3 = $Crop4 = 0
if (-not [string]::IsNullOrWhiteSpace($CropOffsets)) {
    $Crops = $CropOffsets.Split(',')
    $NumCrops = $Crops.Count
    if ($NumCrops -ne 1 -and $NumCrops -ne 2 -and $NumCrops -ne 4) {
        Exit-WithError "Crop offsets must be 1, 2, or 4 comma-separated integers."
    }
    $Crop1 = [int]$Crops[0]
    if ($NumCrops -ge 2) { $Crop2 = [int]$Crops[1] }
    if ($NumCrops -eq 4) { $Crop3 = [int]$Crops[2]; $Crop4 = [int]$Crops[3] }
}

# Check FilterSize
if ($FilterSize -lt 1) { Exit-WithError "FilterSize must be an integer > 0" }

# Check Density
$ApplyDensity = ""
if ($Density -gt 0) {
    $ApplyDensity = "-density $Density"
}

# Invert Logic
$Inversion1 = ""
if ($Invert -ne 0) {
    $Inversion1 = "-negate"
}

# --- Temporary File Setup ---
$TempFile = [System.IO.Path]::GetTempFileName()
# Rename temp file to have image extension (mpc/cache is internal IM format, using png/tiff is safer for general use)
# Using standard image format to avoid MPC/Cache complication on Windows
$TempImg = $TempFile + ".png" 

try {
    # --- Step 1: Read Input ---
    # Read the input image into the temporary image
    $cmdArgs = @("-quiet")
    if ($ApplyDensity) { $cmdArgs += $ApplyDensity.Split(' ') }
    $cmdArgs += $InputFile
    $cmdArgs += "+repage"
    
    # We apply pre-rotation logic later based on dimensions, 
    # but initial inversion happens here if needed.
    if ($Inversion1) { $cmdArgs += $Inversion1 }
    $cmdArgs += $TempImg

    & $IMBinary $cmdArgs
    if ($LASTEXITCODE -ne 0) { Exit-WithError "Failed to read input file." }

    # --- Step 2: Analyze Dimensions ---
    $ww = [int](Get-ImageInfo $TempImg "%w")
    $hh = [int](Get-ImageInfo $TempImg "%h")
    
    # Calc Aspect Ratio (Portrait = 1 if h >= w)
    $IsPortrait = if ($hh -ge $ww) { $true } else { $false }

    # --- Step 3: Rotation ---
    $RotationArgs = ""
    if ($Layout -eq "portrait" -and -not $IsPortrait -and $Rotate -eq "cw") {
        $RotationArgs = "-rotate 90"
    } elseif ($Layout -eq "portrait" -and -not $IsPortrait -and $Rotate -eq "ccw") {
        $RotationArgs = "-rotate -90"
    } elseif ($Layout -eq "landscape" -and $IsPortrait -and $Rotate -eq "cw") {
        $RotationArgs = "-rotate 90"
    } elseif ($Layout -eq "landscape" -and $IsPortrait -and $Rotate -eq "ccw") {
        $RotationArgs = "-rotate -90"
    }

    # --- Step 4: Cropping ---
    $CroppingArgs = ""
    if ($NumCrops -gt 0) {
        $wwc = $ww
        $hhc = $hh
        
        if ($NumCrops -eq 1) {
            $wwc = $ww - (2 * $Crop1)
            $hhc = $hh - (2 * $Crop1)
            $CroppingArgs = "-crop ${wwc}x${hhc}+$Crop1+$Crop1 +repage"
        } elseif ($NumCrops -eq 2) {
            $wwc = $ww - (2 * $Crop1)
            $hhc = $hh - (2 * $Crop2)
            $CroppingArgs = "-crop ${wwc}x${hhc}+$Crop1+$Crop2 +repage"
        } elseif ($NumCrops -eq 4) {
            $wwc = $ww - ($Crop1 + $Crop3)
            $hhc = $hh - ($Crop2 + $Crop4)
            $CroppingArgs = "-crop ${wwc}x${hhc}+$Crop1+$Crop2 +repage"
        }
    }

    # --- Step 5: Grayscale ---
    $MakeGrayArgs = ""
    $CurrentColorspace = (Get-ImageInfo $TempImg "%[colorspace]")
    
    # Check IM Version for set colorspace logic (Simplification: assuming modern IM)
    # Usually -set colorspace RGB is needed before conversions in older versions.
    # We will assume standard behavior.
    
    if ($Grayscale -or $CurrentColorspace -eq "Gray") {
        $MakeGrayArgs = "-colorspace gray -type grayscale"
        $Saturation = 100 # Reset saturation if grayscale
    }

    # --- Step 6: Enhance ---
    $EnhancingArgs = ""
    if ($Enhance -eq "stretch") {
        $EnhancingArgs = "-contrast-stretch 0"
    } elseif ($Enhance -eq "normalize") {
        $EnhancingArgs = "-normalize"
    }

    # --- Step 7: Blurring (Text Smoothing) ---
    $BlurringArgs = ""
    if ($Threshold -ge 0) {
        $BlurringArgs = "-blur 1x65535 -level ${Threshold}x100%"
    }

    # --- Step 8: Background Color ---
    $BgColorArg = $BgColor
    if ($BgColor -eq "image") {
        # Determine color from top left pixel
        $Pixel = Get-ImageInfo $TempImg "%[pixel:u.p{0,0}]"
        $FuzzValCalc = 100 - $Fuzz
        # Complex calculation to average background - simplified here to top-left for PS port
        # To strictly follow script: 
        # convert $tmpA1 -fuzz $fuzzval% +transparent "$bgcolor" -scale 1x1! -alpha off -format "%[pixel:u.p{0,0}]" info:
        $BgColorArg = & $IMBinary $TempImg -fuzz "$FuzzValCalc%" +transparent "$Pixel" -scale "1x1!" -alpha off -format "%[pixel:u.p{0,0}]" info:
    }

    # --- Step 9: Unrotate (Deskew) ---
    $UnrotatingArgs = ""
    if ($Unrotate) {
        if ($Preserve) {
            $UnrotatingArgs = "-background $BgColorArg -deskew 40% -gravity center -background $BgColorArg -compose over -extent ${ww}x${hh}+0+0 +repage"
        } else {
            $UnrotatingArgs = "-background $BgColorArg -deskew 40%"
        }
    }

    # --- Step 10: Sharpening ---
    $SharpeningArgs = ""
    if ($Sharpen -gt 0) {
        $SharpeningArgs = "-sharpen 0x$Sharpen"
    }

    # --- Step 11: Modulation (Saturation) ---
    $ModulationArgs = ""
    if ($Saturation -ne 100) {
        $ModulationArgs = "-modulate 100,$Saturation,100"
    }

    # --- Step 12: Adaptive Blur ---
    $AdaptiveBlurArgs = ""
    if ($AdaptBlur -gt 0) {
        $AdaptiveBlurArgs = "-adaptive-blur $AdaptBlur"
    }

    # --- Step 13: Trim ---
    $TrimmingArgs = ""
    if ($Trim) {
        # Assuming simple trim. The script checks for HDRI to do white-threshold.
        # We will apply a generic white threshold safety just in case.
        $TrimmingArgs = "-white-threshold 99.9% -trim +repage"
    }

    # --- Step 14: Pad ---
    $PaddingArgs = ""
    if ($Pad -gt 0) {
        $PaddingArgs = "-compose over -bordercolor $BgColorArg -border $Pad"
    }

    # --- Step 15: Invert Output ---
    $Inversion2 = ""
    if ($Invert -eq 2) {
        $Inversion2 = "-negate"
    }

    # --- Step 16: Compression ---
    $CompressionArgs = ""
    $Ext = [System.IO.Path]::GetExtension($OutputFile).ToLower()
    if ($Ext -eq ".tif" -or $Ext -eq ".tiff") {
        
        # Normalize compression string for IM
        $CompMap = @{
            "n" = "none"; "l" = "lzw"; "z" = "zip"; "f" = "fax"; "g" = "group4"
        }
        if ($CompMap.ContainsKey($Compression)) { $Compression = $CompMap[$Compression] }
        
        $CompressionArgs = "-compress $Compression"
    }

    # --- Step 17: Final Resize ---
    $ResizingArgs = ""
    if ($Resize -gt 0) {
        $ResizingArgs = "-resize $Resize%"
    }

    # --- FINAL EXECUTION ---
    # The complex convert command in the original script:
    # convert ( $tmpA1 $cropping $makegray $enhancing ) \
    #   ( -clone 0 $setcspace -colorspace gray -negate -lat ${filtersize}x${filtersize}+${offset}% -contrast-stretch 0 $blurring ) \
    #   -alpha off -compose copy_opacity -composite -fill "$bgcolor" -opaque none -alpha off \
    #   $unrotating $sharpening $modulation $adaptiveblurring $resizing $trimming $padding $inversion2 $compressing \
    #   "$outfile"

    $FinalArgs = @()
    $FinalArgs += "-respect-parenthesis"
    
    # Parenthesis 1: Base image preparation
    $FinalArgs += "("
    $FinalArgs += $TempImg
    if ($RotationArgs) { $FinalArgs += $RotationArgs.Split(' ') }
    if ($CroppingArgs) { $FinalArgs += $CroppingArgs.Split(' ') }
    if ($MakeGrayArgs) { $FinalArgs += $MakeGrayArgs.Split(' ') }
    if ($EnhancingArgs) { $FinalArgs += $EnhancingArgs.Split(' ') }
    $FinalArgs += ")"

    # Parenthesis 2: The Mask Generation (LAT filter)
    $FinalArgs += "("
    $FinalArgs += "-clone", "0"
    $FinalArgs += "-colorspace", "gray"
    $FinalArgs += "-negate"
    $FinalArgs += "-lat", "${FilterSize}x${FilterSize}+${Offset}%"
    $FinalArgs += "-contrast-stretch", "0"
    if ($BlurringArgs) { $FinalArgs += $BlurringArgs.Split(' ') }
    $FinalArgs += ")"

    # Compositing
    $FinalArgs += "-alpha", "off"
    $FinalArgs += "-compose", "copy_opacity"
    $FinalArgs += "-composite"
    $FinalArgs += "-fill", "$BgColorArg"
    $FinalArgs += "-opaque", "none"
    $FinalArgs += "-alpha", "off"

    # Post-processing
    if ($UnrotatingArgs) { $FinalArgs += $UnrotatingArgs.Split(' ') }
    if ($SharpeningArgs) { $FinalArgs += $SharpeningArgs.Split(' ') }
    if ($ModulationArgs) { $FinalArgs += $ModulationArgs.Split(' ') }
    if ($AdaptiveBlurArgs) { $FinalArgs += $AdaptiveBlurArgs.Split(' ') }
    if ($ResizingArgs) { $FinalArgs += $ResizingArgs.Split(' ') }
    if ($TrimmingArgs) { $FinalArgs += $TrimmingArgs.Split(' ') }
    if ($PaddingArgs) { $FinalArgs += $PaddingArgs.Split(' ') }
    if ($Inversion2) { $FinalArgs += $Inversion2 }
    if ($CompressionArgs) { $FinalArgs += $CompressionArgs.Split(' ') }

    # Output
    $FinalArgs += $OutputFile

    # Execute
    Write-Host "Processing image..."
    & $IMBinary $FinalArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully created: $OutputFile"
    } else {
        Exit-WithError "ImageMagick failed to process the image."
    }

} finally {
    # Cleanup
    if (Test-Path $TempImg) { Remove-Item $TempImg -Force -ErrorAction SilentlyContinue }
    if (Test-Path $TempFile) { Remove-Item $TempFile -Force -ErrorAction SilentlyContinue }
}