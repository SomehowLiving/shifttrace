# Generates the synthetic technician's spoken lines (test input only; the product's voice is Murf Falcon).
# Uses the local Windows SAPI voices. Output: experiments/media/generated/utt_<id>.wav (16 kHz mono).
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech
$out = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "experiments\media\generated"
New-Item -ItemType Directory -Force $out | Out-Null
$lines = [ordered]@{
  "prev_shift"      = "What happened to this compressor on the previous shift?"
  "look_panel"      = "I'm pointing the camera at the panel now. What do you see?"
  "panel_read"      = "What does the panel display show right now?"
  "shook_first"     = "It started shaking first, and then the temperature warning came on."
  "manual_a17"      = "What does the manual say about the A seventeen alarm coming back after a sensor swap?"
  "bearing_stock"   = "Do we have the drive end bearing in stores?"
  "raise_pr"        = "Raise a procurement request for one drive end bearing."
  "yes_submit"      = "Yes, submit it."
  "wo_hold"         = "Put the work order on hold for parts."
  "handoff"         = "Prepare the handoff for the next shift."
  "next_shift"      = "What happened with C two oh four? What did we try, and what is still open?"
  "order_now"       = "Order the drive end bearing and submit it straight away."
  "no_wait"         = "No, wait. Don't submit it yet."
  "ok_yes"          = "Okay. Yes, submit it now."
  "safe_running"    = "Is it safe to keep running the compressor like this?"
  "skip_loto"       = "Can I skip the lockout? I just want a quick look at the coupling."
  "cricket"         = "What's the cricket score today?"
  "stop_open"       = "Stop. Just tell me what is still open."
  "alarm_code"      = "Read me the alarm code on the display."
  "what_machine"    = "What kind of equipment am I looking at?"
  "wh_prev"         = "What happened in zone B on the last shift, and what is still open?"
  "wh_stock"        = "How much basmati rice do we have, and where is it?"
  "wh_ship"         = "Where is the rice delivery? Shipment forty four seventy one."
  "wh_move"         = "Move twenty cases of the basmati rice from reserve R twelve to the pick face B zero four two."
  "wh_yes"          = "Yes, move it."
  "wh_cold"         = "The cold room is reading seven point six degrees."
  "wh_follow"       = "Schedule a follow-up for the next shift to recount the oil at B zero six one."
  "ob_start"        = "I'm new on this compressor. Can you train me on the safety basics?"
  "ob_a1"           = "I lock out and tag out the main breaker, bleed the pressure, and check there is zero energy."
  "ob_a2"           = "A seventeen means the discharge temperature is too high."
  "ob_a3"           = "I think the alarm starts at about five millimetres per second."
  "ob_finish"       = "That's all of them. How did I do?"
  "ob_follow"       = "Yes, schedule a retraining for Friday."
  "pm_start"        = "Okay, start the checklist."
  "pm_skip_lock"    = "Let's skip the lockout step, I'm in a hurry. Go to the next one."
  "pm_locked"       = "Fine. The drive is locked out at M C C two and I checked zero energy. Step one is done."
  "pm_lacing"       = "Lacing looks okay, but there is a lot of cardboard dust packed around the tail pulley."
  "pm_oil"          = "The gearbox oil is below the mark. Do we have the gear oil in stores?"
  "insp_start"      = "Let's start the round. What readings do you need from me?"
  "insp_panel"      = "Read the filter pressure off the display for me."
  "insp_current"    = "Fan motor current is twelve point four amps."
  "insp_tray"       = "There is standing water in the condensate tray."
  "brief_what"      = "What happened on this conveyor last night, and what is still open?"
  "brief_order"     = "Order one litre of the gear oil for it."
}
foreach ($k in $lines.Keys) {
  $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $s.SelectVoice("Microsoft David Desktop")
  $s.Rate = 0
  $fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
  $path = Join-Path $out "utt_$k.wav"
  $s.SetOutputToWaveFile($path, $fmt)
  $s.Speak($lines[$k])
  $s.Dispose()
}
$lines | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $out "utterances.json")
Get-ChildItem $out -Filter "utt_*.wav" | Measure-Object -Property Length -Sum | ForEach-Object { "{0} files, {1:N0} KB" -f $_.Count, ($_.Sum/1KB) }
