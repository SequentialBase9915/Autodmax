import pygame
import wx
from pygame.math import Vector2
from sw_serial import *
import cv2
import numpy as np
from datetime import date

# Initialize the serial connection and then joysticks
pygame.joystick.init()
joy_count = pygame.joystick.get_count()
if joy_count > 0:   
    xbox_360 = pygame.joystick.Joystick(0)
    xbox_360.init()
    print(xbox_360.get_name())

###############################################################################
# Joystick controls 
###############################################################################

def button_press():
    btn_dict = {
        0:BTN_A,1:BTN_B,2:BTN_X,3:BTN_Y,4:BTN_L,
        5:BTN_R,6:BTN_MINUS,7:BTN_PLUS,8:BTN_HOME}
    # Mapped from XBOX 360 to Switch
    btn_list = []
    for button in btn_dict:
        if xbox_360.get_button(button):
            btn_list.append(btn_dict[button])        
    return (sum(btn_list))

def hat_motion():
    hat_xy = [[-1,0],[1,0],[0,1],[0,-1],[0,0]]
    # X, Y dpad values from XBOX controller
    hat_btn = [DPAD_L,DPAD_R,DPAD_U,DPAD_D,DPAD_CENTER]
    # Corresponding action in Switch controller
    for hat in hat_xy:
        if xbox_360.get_hat(0) == (hat[0],hat[1]):
            trigger_hat = hat_btn[hat_xy.index(hat)]
    return trigger_hat

def z_axis():
    if xbox_360.get_axis(2) >= .5:
        z_btn = BTN_ZL
    elif xbox_360.get_axis(2) <= -.5:
        z_btn = BTN_ZR
    else:
        z_btn = 0
    return z_btn
    
def stick_move():
    left_x = xbox_360.get_axis(0)
    left_y = xbox_360.get_axis(1)
    right_x = xbox_360.get_axis(4)  
    right_y = xbox_360.get_axis(3)

    axis_list = [[left_x,left_y],[right_x,right_y]]

    angle_list = []    
    for stick in axis_list:
        vec = Vector2(stick[0],stick[1])
        rad, ang = vec.as_polar()
        if ang <= 0:
            ang = (-1) * ang
        elif ang >= 0:
            ang = 360 - ang
        angle_list.append(ang)

 # Need to input intensity -> value between 50 (0x32) and 255 (0xFF).
 # rad adjusted to 1 if over 255 as it resets above this value.
    stick_intsy = []
    for stick in axis_list:
        power = Vector2(stick[0],stick[1])
        rad, ang = power.as_polar()
        if rad > 1:
            rad = 1
        intsy = int(rad * 255)
        stick_intsy.append(intsy)

# read the x and y from each stick and if > 0 consider pressed
# then send the stick signal
#if blank send center command (shared for L and R as it's the same value)
    state_axes = []
    for joy in axis_list:
        which_stick = axis_list.index(joy)
        state_joy = 0
        for axis in joy:
            if -1 <= axis <= -0.1 or 0.1 <= axis <= 1:
                state_joy += 1
            else:
                state_joy += 0
        if state_joy > 0:
            state_axes.append(
                stick_angle(int(angle_list[which_stick]),
                stick_intsy[which_stick], which_stick)
                )
        else:
            state_axes.append(LSTICK_CENTER)
    joy_cmd = state_axes[0] + state_axes[1]
    return joy_cmd

def timemov(direction, length, stick=0):    
    i = 0
    while i < length:
        cmd = stick_angle(direction, 0xFF,stick)
        send_cmd(cmd)
        i += 1
    
def btn_press(button, wait):
    send_cmd(button)
    p_wait(0.1)
    send_cmd(BTN_NONE)
    p_wait(wait)

def stick_press(dpad,wait):
    send_cmd(dpad)
    p_wait(0.05)
    send_cmd(LSTICK_CENTER)
    p_wait(wait)
    
def hat_press(hat,wait):
    send_cmd(BTN_NONE + hat+ LSTICK_CENTER + RSTICK_CENTER)
    p_wait(0.07)
    send_cmd(DPAD_CENTER)
    p_wait(wait)
    
###############################################################################
# Keyboard inputs
###############################################################################
def kbd_input(key_name):
    if key_name == "0":
        print("Starting egg hatching macro...")
        hatch_egg_macro()
    if key_name == "2":
        print("Starting release macro...")
        release_macro()
    if key_name == "3":
        print("Next loop")
        encounter_loop()
    if key_name == "5":
        print("Starting batch hatching macro")
        batch_hatch_macro()
    if key_name == "7":
        print("Starting egg fetching macro...")
        get_eggs_macro()
    elif key_name == "w":
        cmd = stick_angle(90, 0xFF,0)
        send_cmd(cmd)
    elif key_name == "s":
        cmd = stick_angle(270, 0xFF,0)
        send_cmd(cmd)
    elif key_name == "a":
        cmd = stick_angle(180, 0xFF,0)
        send_cmd(cmd)
    elif key_name == "d":
        cmd = stick_angle(360, 0xFF,0)
        send_cmd(cmd)
    elif key_name == "q":
        send_cmd(RSTICK_L)
    elif key_name == "e":
        send_cmd(RSTICK_R)
    elif key_name == "up":
        hat_press(DPAD_U,0.01)
    elif key_name == "down":
        hat_press(DPAD_D,0.01)
    elif key_name == "left":
        hat_press(DPAD_L,0.01)
    elif key_name == "right":
        hat_press(DPAD_R,0.01)
    elif key_name == "return":
        btn_press(BTN_A,0.05)
    elif key_name == "backspace":
        btn_press(BTN_B,0.05)
    elif key_name == "x":
        btn_press(BTN_X,0.05)
    elif key_name == "y":
        btn_press(BTN_Y,0.05)
    elif key_name == "r":
        btn_press(BTN_R,0.05)
    elif key_name == "l":
        btn_press(BTN_L,0.05)
    elif key_name == "-":
        btn_press(BTN_MINUS,0.05)
    elif key_name == ";":
        btn_press(BTN_PLUS,0.05)
    elif key_name == "h":
        btn_press(BTN_HOME,0.05)
###############################################################################
# Macros
###############################################################################
        
class swmacro:
    app = wx.App() #One App per process, may need to move further up in future
        
    def __init__(self,msg,title,lower,upper):
        self.msg = msg
        self.title = title
        self.lower = lower
        self.upper = upper
        
    def macro_prompt(self):
        frame = wx.Frame(None, -1, 'win.py')
        frame.SetSize(0,0,100,100)
        dlg = wx.TextEntryDialog(frame, self.msg,self.title)
        if dlg.ShowModal() == wx.ID_OK:
            dlg.GetValue()
            int_input = int(dlg.GetValue())
            if int_input == None:
                return None
            if int_input in range(self.lower,self.upper+1):
                return int_input
            else:
                dialog = wx.MessageDialog(
                    frame,"Incorrect amount", 'Error',wx.OK|wx.ICON_ERROR
                    )
                dialog.ShowModal()
                dialog.Destroy()
                return swmacro.macro_prompt(self)

def hatch_egg_macro():
#Needs full party, town map first option, start w/o bike, egg ready to pick up
    egg_group = swmacro(
        'Choose Egg Group # (Starters(1) Longer(2) Very long(3): ',
        'Egg cycle type',1,3
        )
    group = egg_group.macro_prompt()
    egg_hatch = swmacro('Number to hatch','Egg hatch count',1,600)
    eggs = egg_hatch.macro_prompt()

    if egg_group == None or egg_hatch == None:
        print("Macro aborted due to no entry")
        return None

    steps_dict = {1:12800,2:14800,3:21200}
    try:
        steps = steps_dict.get(group)
        for i in range(eggs):
            btn_press(BTN_X,1) #Open menu - assuming map is first btn available
            btn_press(BTN_A,3) #Open map
            btn_press(BTN_A,1.5) #Select location assuming nursery is location
            btn_press(BTN_A,1) #Confirm
            btn_press(BTN_A,3) #Travel
            timemov(260,200) #Move back to egg person
            btn_press(BTN_L,1.3) #Swivel screen around to face
            btn_press(BTN_A,1.1) #open conversation
            btn_press(BTN_A,2.2) #next line
            btn_press(BTN_A,3.2) #"Yes" to accept egg
            btn_press(BTN_A,2.2) #Confirmation
            btn_press(BTN_A,1.3) #Add to roster
            btn_press(BTN_A,2.2) #Confirmation
            stick_press(LSTICK_D,0.7) #Down 1 slot
            stick_press(LSTICK_D,0.7) #Down another slot (now on 3rd slot)
            btn_press(BTN_A,2.5) #Confirmation
            btn_press(BTN_A,2.5) #Confirmation    
            btn_press(BTN_A,2) #Confirmation
            send_cmd(stick_angle(270, 0xFF,0))#turn around
            p_wait(0.3)
        #        btn_press(BTN_PLUS,1) #Get on bike
            timemov(250,700) #Move into place
            btn_press(BTN_PLUS,1.2)    
            # 360 Circle @ Full Intensity
            for r in range(steps):
                send_cmd(LSTICK_L+RSTICK_R) 
            btn_press(BTN_A,18)#After egg hatches
            btn_press(BTN_A,5)#After egg hatches
            btn_press(BTN_PLUS,2.3)
            print(i)
    except:
        print("Incorrect Group")
          
def get_eggs_macro():
    get_egg = swmacro('Number of eggs to get','Egg fetching',1,150)
    egg_count = get_egg.macro_prompt()
    if egg_count == None:
        print("Macro aborted due to no entry")
        return None
    print("Getting %s eggs" % egg_count)
    #Needs to have egg ready. full slots
    for g in range (egg_count):      
            btn_press(BTN_X,1) #Open menu - assuming map is first btn available
            btn_press(BTN_A,3) #Open map
            btn_press(BTN_A,1.5) #Select location assuming nursery is location
            btn_press(BTN_A,1) #Confirm
            btn_press(BTN_A,3) #Travel
            timemov(260,200) #Move back to egg person
            btn_press(BTN_L,1) #Swivel screen around to face
            btn_press(BTN_A,1) #open conversation
            btn_press(BTN_A,2) #next line
            btn_press(BTN_A,3.2) #"Yes" to accept egg
            btn_press(BTN_A,2) #Confirmation
            stick_press(LSTICK_D,0.5) #Down 1 slot
            btn_press(BTN_A,1.5) #Confirm            
            btn_press(BTN_A,2) #Confirm
            btn_press(BTN_A,1) #exit conversation            
            send_cmd(stick_angle(270, 0xFF,0))#turn around
            p_wait(0.2)
            timemov(250,700) #Move into place
            btn_press(BTN_PLUS,1)    
            # 360 Circle @ Full Intensity
            r = 0
            for r in range (3000):
                #estimated hatch rate 256 steps x 5 sets at 80% rate
                # and using ratio of steps with egg hatching 
                send_cmd(LSTICK_L+RSTICK_R)
            btn_press(BTN_PLUS,1)
   #return egg_count

def batch_hatch_macro():
    steps = 13000
    #Start at current inventory (2nd position down)
    #Eggs need to be in second column, with blank column at first
    btn_press(BTN_Y,1) #Change cursor
    btn_press(BTN_Y,1) #Change again
    btn_press(BTN_A,1) #Select first item
    hat_press(DPAD_D,0.3)
    hat_press(DPAD_D,0.3)
    hat_press(DPAD_D,0.3)
    hat_press(DPAD_D,0.3)#Move down to fifth item
    btn_press(BTN_A,1)#Select and pick up
    hat_press(DPAD_R,0.5)#Move over to inventory
    hat_press(DPAD_U,0.5) #Shift up
    btn_press(BTN_A,1) #Set down in box

    hat_press(DPAD_R,0.3) #Move to row of eggs
    btn_press(BTN_A,1) #Select first egg
    hat_press(DPAD_D,0.3)
    hat_press(DPAD_D,0.3)
    hat_press(DPAD_D,0.3)
    hat_press(DPAD_D,0.3)#Move down to fifth egg
    btn_press(BTN_A,1) #Select and pick up
    hat_press(DPAD_L,0.5)
    hat_press(DPAD_L,0.5)#Move to the てもち list
    hat_press(DPAD_D,0.3)#Position for placement
    btn_press(BTN_A,1) #Place in active roster
    btn_press(BTN_B,1.5)
    btn_press(BTN_B,1.5)
    btn_press(BTN_B,1.5) #get back to overworld
    btn_press(BTN_PLUS,1) #Get on bike
    for r in range(steps):
        send_cmd(LSTICK_L+RSTICK_R)
    for i in range(4):
        btn_press(BTN_A,18)#After egg hatches
        btn_press(BTN_A,6)#After egg hatches
        #Timing is currently INCORRECT, needs to be a bit longer and test
        if i != 4:
            for r in range(200):
                send_cmd(LSTICK_L+RSTICK_R)
        else:
            btn_press(BTN_PLUS,2.3)

def encounter_loop():
    
    i = 0
    try:
        while True:    
        #Start in battle in order to shiny check
            btn_press(BTN_HOME,0.7) #Go to home screen
            btn_press(BTN_X,0.8) #bring up exit menu
            btn_press(BTN_A,2.8) #select exit
            btn_press(BTN_A,1) #bring up profile select
            btn_press(BTN_A,17.5) #open game
            btn_press(BTN_A,6.5) #load game
            btn_press(BTN_A,5) #open menu
            btn_press(BTN_A,1.5) #confirm
            #btn_press(BTN_A,1.1) #confirm (Regidrago)
            #btn_press(BTN_A,1.5) #confirm (Regidrago)            
            btn_press(BTN_A,13.5) #start encounter
            #set cv2 for screenshot
            cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            ret, frame = cap.read()
            img_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask_color1 = np.asarray([14,0,50])
            mask_color2 = np.asarray([24,255,255])
            mask = cv2.inRange(img_hsv, mask_color1,mask_color2)
            color_pct = (cv2.countNonZero(mask)/(img_hsv.shape[0] * img_hsv.shape[1]))*100
            print(str(i)+' {:.5f}'.format(color_pct))
            if i == 0:
                if color_pct < 1.5:
                    cv2.imshow("Shiny",shiny_pic)
                    break
            if i != 0:
                if color_pct < 1.6:
                    cv2.imshow("Shiny",shiny_pic)
                    break
            p_wait(3)
            i += 1
    except KeyboardInterrupt:
        pass

def release_macro():
    #Need to be at start position of box for deleting correctly
    #Look into adding support for an arbitrary start point
    release_pokemon = swmacro(
        'Number of Pokemon to release',
        'Pokemon Count',1,600
        )
    release_count = release_pokemon.macro_prompt()
    if release_count == None:
        print("Macro aborted due to no entry")
        return None
    r = 1
    b = 1    
    try:
        for i in range(release_count):
            btn_press(BTN_A,0.5)
            hat_press(DPAD_U,0.2)
            hat_press(DPAD_U,0.2)
            btn_press(BTN_A,0.7)
            hat_press(DPAD_U,0.2)
            btn_press(BTN_A,1.2)   
            btn_press(BTN_A,0.9)
            print("Released %s" % i)
            if  (i+1) % 6 == 0 and (i+1) % 30 != 0:
                #Added 1 to account for r starting at 0
                hat_press(DPAD_D,0.8)
                print("%s end of row" % (i+1))
                r += 1
                print(r)
            elif (i+1) % 30 == 0:
                hat_press(DPAD_D,0.3)
                hat_press(DPAD_D,0.3)
                hat_press(DPAD_D,0.3)            
                hat_press(DPAD_R,0.3)
                hat_press(DPAD_R,0.3)
                btn_press(BTN_R,0.8)
                print("%s end of box" % (i+1))
                b += 1
                r += 1
                print(b)
            else:      
                    if (b % 2 != 0 and r % 2 == 0) or (r % 2 != 0 and b % 2 == 0):
                        hat_press(DPAD_L,0.3)
                        print("%s next value (left)" % (i+1))
                    else:
                        hat_press(DPAD_R,0.3)
                        print("%s next value (right)" % (i+1))
    except:
        print("Incorrect value")



def watt_farmer():
    i = 0
    day = 1
    while i < 1000:
        print(f"Current day is {day}")
        if day == 1:
            btn_press(BTN_A,1.1)
            btn_press(BTN_A,3)
        else:
            btn_press(BTN_A,1)
            btn_press(BTN_A,1)
            btn_press(BTN_A,1.5)
            btn_press(BTN_A,3)    
        # Enter battle search for first time (must be facing den)
        btn_press(BTN_HOME,1)
        hat_press(DPAD_R,0.3)
        hat_press(DPAD_R,0.3)
        hat_press(DPAD_D,0.4)
        hat_press(DPAD_R,0.3)
        btn_press(BTN_A,1)
        # Brings to settings screen
        for r in range (14): 
            hat_press(DPAD_D,0.2)
        # To quickly scroll down the list
        hat_press(DPAD_R,0.3)
        hat_press(DPAD_D,0.3)
        hat_press(DPAD_D,0.3)
        hat_press(DPAD_D,0.3)
        hat_press(DPAD_D,0.3)
        btn_press(BTN_A,0.6)
        hat_press(DPAD_D,0.3)
        hat_press(DPAD_D,0.3)
        btn_press(BTN_A,0.6)
        # Brings up time settings
        hat_press(DPAD_R,0.2)
        hat_press(DPAD_R,0.2)
        hat_press(DPAD_U,0.2)
        btn_press(BTN_A,0.2)
        btn_press(BTN_A,0.2)
        btn_press(BTN_A,0.2)
        btn_press(BTN_A,0.2)
        btn_press(BTN_HOME,1.4)
        # Moves date up and moves back to home screen
        btn_press(BTN_A,1.5)
        btn_press(BTN_B,1)
        btn_press(BTN_A,4)
        # Exit battle
        if day == 31:
            day = 1
        else:
            day += 1
        i += 1
