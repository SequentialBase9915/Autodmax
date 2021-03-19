#!/usr/bin/env python3
import os, wx, cv2, pygame
from datetime import datetime
import locale 
from sw_joystick import (ser, serial_connect, kbd_input, btn_press, 
    button_press, stick_move, hat_motion, z_axis, watt_farmer, BTN_NONE, send_cmd)

#Must set this before importing autodmax to get to work correctly
locale.setlocale(locale.LC_ALL, 'en_US')
from autodmax import ad_main as ad

###############################################################################

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

class myFrame(wx.Frame):
    
    def __init__(self, title, pos, size):
        wx.Frame.__init__(
            self, parent=None, id=-1, title=title,
            size=size, style = wx.NO_BORDER | wx.STAY_ON_TOP
            )
        
    def pygm(self):
        # Note GetHandle() method of a control in the window/frame,
        # not the wxFrame itself
        self.hwnd = self.GetHandle()
        os.environ['SDL_VIDEODRIVER'] = 'windib'
        os.environ['SDL_WINDOWID'] = str(self.hwnd)
        serial_connect()
        pygame.init()
        self.display = pygame.display.set_mode((1,1),pygame.NOFRAME)
        pygame.display.update()
        self.SetFocus()
        
app = wx.App(0)
frame = myFrame(title = u'Pygame', pos=(50, 60), size=(20, 20))
frame.pygm()
app.SetTopWindow(frame)
frame.Show()

def video_loop(cap):
    __, frame = cap.read()
    # FPS x seconds
    multiplier = 5 
    # Gets current frame and rounds
    frame_num = int(round(cap.get(1)))
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    if frame_num % multiplier == 0:
        ad.screen_check(hsv,ad.lookups,ad.text,cap)
        
###############################################################################   
# Start pygame and setup video/fonts for display     
###############################################################################
def input_loop():
    while True:  
        if ad.var.autodynamax_switch == 1:
            video_loop(cap)          
        events = pygame.event.get() #[pygame.jkevent.wait()]
        # Commented code smooths out the handling of events
        for event in events:
            keys_pressed = pygame.key.get_pressed()
            if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                key_name = pygame.key.name(event.key)
                if event.type == pygame.KEYDOWN:
                    # Screenshot with timestamp
                    if key_name == "p":
                        dateTimeObj = datetime.now()
                        
                        stamp = str(dateTimeObj.month) + '.' + \
                                str(dateTimeObj.day) + '.' + \
                                str(dateTimeObj.hour) + 'H' + \
                                str(dateTimeObj.minute) + 'M' + \
                                str(dateTimeObj.second) + 'S'
                        
                        __, frame = cap.read()
                        cv2.imwrite(ad.save_dir + '\\' + stamp + '.PNG',frame)
                    # Flip for autodynamax 
                    if key_name == "j":
                        if ad.var.autodynamax_switch == 0:
                            print("Turning autodynamax script on")
                            ad.var.autodynamax_switch = 1
                            pass
                        else:
                            print("Turning autodynamax script off")
                            ad.var.autodynamax_switch = 0
                    # Series to join dmax adventure raid, used after switch.        
                    if key_name == "k":
                        ad.join_battle()
                    # Key for starting watt farming script    
                    if key_name == "o":
                        watt_farmer()

                    # For other inputs, look at the sw_joystick reference    
                    kbd_input(key_name)

                # For movement, allows smoother switching of directions
                if event.type == pygame.KEYUP and any(keys_pressed):
                    if keys_pressed[pygame.K_d] == 1:
                        kbd_input("d")
                    if keys_pressed[pygame.K_a] == 1:
                        kbd_input("a")
                    if keys_pressed[pygame.K_w] == 1:
                        kbd_input("w")
                    if keys_pressed[pygame.K_s] == 1:
                        kbd_input("s")
                # Stops movement if all keys are released
                if event.type == pygame.KEYUP and not any(keys_pressed):
                    btn_press(BTN_NONE,0.01)
            # Main looping command input from joystick           
            if event.type in (
                pygame.JOYAXISMOTION,pygame.JOYHATMOTION,
                pygame.JOYBUTTONUP,pygame.JOYBUTTONDOWN
                ):
                send_cmd(
                    stick_move() + button_press() + hat_motion() + z_axis()
                    )

    pygame.quit()
    ser.close()
###############################################################################
if __name__ == "__main__":
    input_loop()
    app.MainLoop()
    
