## Subtitle Parsing to Transcript
Quick python script for taking a zipped folder of srt formatted subtitles and converting them to a readable transcript.

### How to Run
<code> python str_parse.py --filein &#60;full path to your zipped subtitiles file&#62; [--fileout &#60;where you want the subtitle to output to&#62; 
</code>]

By default the transcript will output to the home folder as transcript.txt.

Dependencies
---
#### Python

python==2.7

chardet==3.0.4

pkg-resources==0.0.0

pysrt==1.1.1

PyYAML==5.1.2
#### Nix
unzip
