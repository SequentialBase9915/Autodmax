# Autodmax  
オートダイマックス（Autodmax）は剣盾のダイマックスアドベンチャーを自動化するスクリプトです。  
Automated Dynamax Adventure script for SwSh.  
  
Notes  
漢字モードのみの対応になります。ひらがなや他の言語は対応していません。  
自分のパソコン環境でしか検証しておらず、動作がビデオカードキャプチャーカードやCPUなどに影響されやすいため、  
現状他のパソコン環境で正しく作動しない可能性が高いです。  
  
This script is limited to Japanese only (Kanji version), and is highly dependent on specific video input card settings and processor timings.  
Please do not expect this to work as is without further modification. There is no support for this program so please do not ask for edits.  
  
操作をするにはArduino R3やTeensyなどのマイコンボードとUSB-TTLのシリアルアダプターが必要です。  
これらの設定方法の情報と参考ページは今後載せる予定ですが、整理中のため現時点では抜けています。  
  
The Joystick hex file and directions for setting up serial are not currently included.  
The needed files and links to resources used will be added in the future.  
  
Acknowledgements:  
javmarina: https://github.com/javmarina/Nintendo-Switch-Remote-Control  
Hexファイルの書き込みの仕方やArduinoとUSB-TTLアダプター接続の仕方などについて詳細の情報を提供しています。  
For reference joystick hex, steps to correctly flash Arduino R3 and guidance on sequence to connect serial + Arduino to PC and Switch.  
  
wchill: https://github.com/wchill/SwitchInputEmulator  
Hexファイルを元々入手したプロジェクトです。Arduinoへの書き込み方も参考になりました。  
Original source for joystick hex and flashing.  
  
progmem: https://github.com/progmem/Switch-Fightstick  
上の二つのプロジェクトのベースとなっています。以下のリンクがそのプロジェクトを紹介しています。  
Inspiration for above work, link describing project shown below.  
https://blog.feelmy.net/control-nintendo-switch-from-computer/  

Pokemon Automation team: https://github.com/PokemonAutomation/AutoMaxLair  
Thanks to the team here for amazing ideas in the chat such as ball-saver mode etc.! This is a much more robust and feature capable solution, if you want something out of the box look here!  
