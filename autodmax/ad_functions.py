from autodmax.ad_data import *
from sw_joystick import *
import numpy as np
import cv2
import pandas as pd
from datetime import datetime
###############################################################################
#Main class for matching images to get result for further processing.
class Img_match(object):
    def __init__(self, image, area):
        self.image = image
        self.area = area
        self.index = 0
        self.multiples = [26,28,51,53,105,110,122,264,550,618,745,797]

    def get_contours(self,check_area):
        gray = cv2.cvtColor(check_area, cv2.COLOR_BGR2GRAY)
        ret, thresh_img = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        edges = cv2.Canny(thresh_img,20,200)
        contours, hierarchy = cv2.findContours(
            edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
        return contours
        
    def get_original_contours(self):
        check_area = self.image[
            self.area[0]:self.area[1],self.area[2]:self.area[3]
            ]
        original_contours = self.get_contours(check_area)
        return original_contours

    def match_contours(self,compare_img,contours):
        compare_contours = self.get_contours(compare_img)
        if len(contours) != len(compare_contours) or contours == []:
            return 100
        else:
            n = 0
            match_amount = 0
            for i in contours:
                match_amount += cv2.matchShapes(
                    contours[n],compare_contours[n],1,0.0
                    )
                n += 1
            return match_amount

    def lookup(self,search_list,lu_list,threshold):
        contours = self.get_original_contours()
        lu_index = self.index
        for item in search_list:
            match_amount = self.match_contours(item,contours)
            if match_amount < threshold:
                match_result = lu_list[lu_index]
            lu_index += 1
        return match_result
    
###############################################################################
class Pokemon(object):
    def __init__(self, identifier, name, level=65):
        self.name = name
        self.dex = identifier[0]
        self.form = identifier[1]
        self.level = level
        self.attacks = []
        self.attack_names = []
        self.weakness_table = []
        self.STAB_type = []
        self.base_stats = []
        self.get_attacks()
        self.get_weaknesses()

#Stat formula: HP = ((((Base x 2) + IV + (EV/4)) * Level) / 100) + Level + 10
#Other stats = (((((Base x 2) + IV + (EV/4)) * Level) / 100) + 5) * Nature
#Adjusted for program: HP = ((((Base x 2) + IV) * Level) / 100) + Level + 10
#Other stats = ((((Base x 2) + IV) * Level) / 100) + 5
#Values are rounded down in each step if decimal
# Adjusted stats for lvl 65.
        
    def get_attacks(self):
        attack_list = df_dex[
            (df_dex['Dex'] == self.dex)&(df_dex['Form'] == self.form)
            ].values
        self.name = attack_list[0][1]
        self.attack_names = attack_list[0][3:7].tolist()
        self.STAB_type = attack_list[0][8:10]
        self.base_stats = attack_list[0][11:17]       
        self.base_stats[0] = int(
            ((self.base_stats[0] * 2 + 31) * self.level) / 100
            + self.level + 10
            )
        for i in range(1,6):
            self.base_stats[i] = int(
                ((self.base_stats[i] * 2 + 31) * self.level) / 100 + 5
                )
        
        for i in range(len(self.attack_names)):
            move_name = self.attack_names[i]
            move_strength = df_moves.loc[move_name,'Type':'PP'].to_list()
            self.attacks.append(move_strength)
        
    def get_weaknesses(self):
        typing = df_dex.loc[
            df_dex['Dex'] == self.dex,'Type 1':'Type 2'
            ].fillna('None').values.tolist()[0]
        #print(self.name+" type is",typing)
        type_multipliers = []
        type_names = df_types.columns.to_list()
        for item in typing:
            multipliers = df_types.loc[item].to_list()
            type_multipliers.append(multipliers)
        type_multipliers = np.multiply(type_multipliers[0],type_multipliers[1])
        self.weakness_table = dict(zip(type_names,type_multipliers))



    def get_best_move(self, defender_mon):
        #Full attack modifier is
        #Modifier = Tgt x Weather x Crit x rnd. x STAB x Type x Burn x other
        #Current modifier check will be Modifier = Target x STAB
        #Third step will check attacker's sp/phys and defender's sp/phys
        pp = []
        adj_atk_str = []
        core_str = 1
        override_moves = ["wide guard",]
        
        for move in self.attacks:
            override = 0
            # Move strength calculation
            if move[2] == "--" or move[4] < 1:
                adj_move = 0
            elif move[2] == "Variable":
                adj_move = 10
            elif move[2] == "Guard":
                # Adjustment to be able to use Wide-guard if AoE boss.
                aoe_mons = [382,383,484,]
                if defender_mon.dex in aoe_mons:
                    adj_move = 500
                    override = 1
                else:
                    adj_move = 0
            else:
                if move[0] in self.STAB_type and move[0] != 'Normal':
                    adj_move = float(move[2])*1.5
                else:
                    adj_move = move[2]
                    
            # Physical/Special ratio calculation         
            if move[1] == "Physical":
                core_str = float(
                    int(self.base_stats[1]) / int(defender_mon.base_stats[2])
                    )
            elif move[1] == "Special":
                core_str = float(
                    int(self.base_stats[3]) / int(defender_mon.base_stats[4])
                    )                  

            # Full move power calculation including type weakness
            if override == 1:
                adj_atk_str.append(int(adj_move))
            else:
                adj_atk_str.append(
                    int(
                        core_str * adj_move *
                        defender_mon.weakness_table.get(move[0])
                        )
                    )

            # Initial population of pp for move
            pp.append(move[4])
            
        adj_move_list = dict(
            zip(
                [name.title() for name in self.attack_names],
                zip(adj_atk_str,pp)
                )
            )
        
        best_move = max(adj_move_list, key=adj_move_list.get)
        best_move_index = self.attack_names.index(best_move.lower())
        print("Moves list:",adj_move_list)
        return best_move, adj_atk_str[best_move_index], best_move_index

    def use_move(self,defender_mon):
        sel_move, attack_strength, sel_index = self.get_best_move(defender_mon)
        
        return sel_move, sel_index
###############################################################################
def scan(cap,start,stop,selection_list,names,shapes):
    ret, frame = cap.read() 
    for i in range(start,stop):
        form = 'normal'
        check = Img_match(frame,names[i])
        match = check.lookup(
            assets_dict["dex_nums_img_s"],assets_dict["dex_nums_s"],0.01
            )
        if match in check.multiples:
            check.area = shapes[i]
            form = check.lookup(
                assets_dict["select_form_shapes"],
                assets_dict["select_form_list"],
                0.00001
                )[1]
        selection_list[i] = [match,form]
        
def initial_select_screen(cap):
    # Set boss for evaluation (Level is set to 70)
    boss_mon = Pokemon(planned_boss, "Boss", 70) 
    initial_select = [0,0,0]
    mon_names = [[313,348,930,1200],[595,630,930,1200],[875,910,930,1200]]
    mon_shapes = [[165,312,922,1065],[445,594,922,1065],[727,874,922,1065]]
            
    # Lookup 2nd and 3rd entries first after selection becomes available
    # then store results.
    scan(cap,1,3,initial_select,mon_names,mon_shapes)   
    # Press DPAD to reposition and then take re-read to get first mon info
    hat_press(DPAD_D,0.6)
    scan(cap,0,1,initial_select,mon_names,mon_shapes) 
    # Create a list for maximum values and then run a comparison
    # on move strength of best move vs. boss.
    max_list = []
    for mon in initial_select:
        max_list.append(Pokemon(mon,"Player").get_best_move(boss_mon)[1])
    #Select best mon and set player mon based on maximum value in list
    best_mon_pos = max_list.index(max(max_list))
    best_mon = initial_select[max_list.index(max(max_list))]
    player_mon = Pokemon(best_mon, "Player")
    if best_mon_pos == 0:
        hat_press(DPAD_U,0.6)
        btn_press(BTN_A,0.6)
    elif best_mon_pos == 1:
        btn_press(BTN_A,1)
    else:
        hat_press(DPAD_D,0.6)
        btn_press(BTN_A,0.6)
    print(
        f"Pokemon number {str(best_mon_pos+1)}, {player_mon.name} was selected"
        )
    return player_mon, boss_mon

###############################################################################

def switch_select_screen(cap,current):
    #Set boss for evaluation
    boss_mon = Pokemon(planned_boss, "Boss", 70)
    max_list = []
    
    switch_select = [[current.dex,current.form],0]
    mon_names = [[370,410,935,1170],[650,690,935,1170]]
    mon_shapes = [[224,373,922,1065],[506,652,922,1065]]
            
    scan(cap,1,2,switch_select,mon_names,mon_shapes)
    
    max_list.append(current.get_best_move(boss_mon)[1])
    max_list.append(
        Pokemon(switch_select[1],"Player").get_best_move(boss_mon)[1]
        )
    #Select best mon and set player mon based on maximum value in list
    best_mon = switch_select[max_list.index(max(max_list))]
    if best_mon == switch_select[1]:
        player_mon = Pokemon(best_mon, "Player")
        print("Will exchange for better mon {}.".format(player_mon.name))
        btn_press(BTN_A,1)
    else:
        player_mon = current
        print("Will keep current mon {}.".format(player_mon.name))
        btn_press(BTN_B,1)
    return player_mon      

###############################################################################
# Process for checking battle screen names (larger elements)    
def battle_screen_name(cap):
    
    ret, frame = cap.read() 
    form = 'normal'
    battle_name_area = [105,180,380,800]
    battle_mon_shape = [85,240,170,355]
    battle_abilities = [110,237,395,830]

    battle_check = Img_match(frame,battle_name_area)
    match = battle_check.lookup(
        assets_dict["dex_nums_img"],assets_dict["dex_nums"],0.01
        )
    if match in battle_check.multiples:
        if match == 550 or match == 745:
            battle_check.area = battle_mon_shape
            form = battle_check.lookup(
                assets_dict["battle_form_shapes"],
                assets_dict["battle_form_list"],0.01
                )[1]
        else:
            battle_check.area = battle_abilities
            form = battle_check.lookup(
                assets_dict["battle_form_shapes"],
                assets_dict["battle_form_list"],0.01
                )[1]
    opponent_mon = Pokemon([match,form],"Opponent")
    return opponent_mon

###############################################################################
def catch_screen_check(cap):
    ret, frame = cap.read()
    catch_text_area = [90,155,1110,1700]
    catch_scr = Img_match(frame,catch_text_area)
    contours = catch_scr.get_original_contours()
    check = catch_scr.match_contours(
        assets_dict["catch_screen_text"],contours
        )
    if check < 1:
        return True
    else:
        return False

###############################################################################
def non_zero(item):
    mask = cv2.inRange(item,np.asarray([10,10,10]),np.asarray([255,255,255]))
    value = cv2.countNonZero(mask)
    return value  

###############################################################################
# Read pp value from 4 attacks available.
def battle_current_pp(cap):
    ret, frame = cap.read()
    current_pp = []
    atks = [
        [670,725,1735,1880],[770,832,1735,1880],
        [875,935,1735,1880],[982,1035,1735,1880]
        ]
    atk_blk = [
        [662,672,1750,1850],[760,770,1750,1850],
        [865,875,1750,1850],[970,980,1750,1850]
        ]
    i = 0
    for attack in atks:
        blk_range = frame[
            atk_blk[i][0]:atk_blk[i][1],atk_blk[i][2]:atk_blk[i][3]
            ]
        
        mask = cv2.inRange(
            blk_range,np.asarray([0,0,0]),np.asarray([0,0,0])
            )
        
        val = int(
            (cv2.countNonZero(mask)/(blk_range.shape[0]*blk_range.shape[1]))
            *100
            )
        
        if val != 100:
            match = 0
            
        else:
            # This breaks sometimes where it sees all black.
            # Except loop in place to deal with this.
            try:
                check = Img_match(frame,attack)
                match = check.lookup(
                    assets_dict["move_pp_values"],
                    assets_dict["move_pp_nums"],
                    0.01
                    )
            except:

                match = 0
        current_pp.append(match)
        i += 1
    return current_pp
###############################################################################
# Command execution, for simplified lists of commands.
# This has some overlap with sw_joystick and should be merged at some point
def execute_commands(command_list):
    cmd_types = {
        "A":BTN_A,"B":BTN_B,"X":BTN_X,"Y":BTN_Y,"R":BTN_R,"L":BTN_L,
        "DD":DPAD_D,"DU":DPAD_U,"DR":DPAD_R,"DL":DPAD_L,"H":BTN_HOME
        }
    for command in command_list:
            #print(f"Pressing {command[0]} for {command[1]}")
            if command[0][0] == "D":
                hat_press(cmd_types[command[0]],command[1])
            else:    
                btn_press(cmd_types[command[0]],command[1])
################################################################################
# Below functions are for cleaning up image and
# running comparison by type to get list for directions
def cleanup_img(img):
    kernel = np.ones((2,2),np.uint8)
    morph = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    _,thresh = cv2.threshold(morph, 254, 255, cv2.THRESH_BINARY)
    edges = cv2.Canny(thresh,200,125)
    return edges

def simple_match(img,cmp):
    clean_ref = cleanup_img(img)
    clean_cmp = cleanup_img(cmp)
    match_level = cv2.matchTemplate(clean_ref,clean_cmp,cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_level)
    return max_val

def dir_type_match(img):
    i = 0
    results = {}
    for item in assets_dict["dir_type_imgs"]:
        cmp = cleanup_img(item)
        res = cv2.matchTemplate(img,cmp,cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        results[assets_dict["dir_type_names"][i]] = [max_val,max_loc[1]]
        #Returns the best match and the y height, for use in determining paths
        i += 1
    best_match = list(results.keys())[
        list(results.values()).index(max(results.values()))
        ]
    return [best_match, results[best_match][1]]

###############################################################################
# Time function for timestamp
def get_time():
    dateTimeObj = datetime.now()
    stamp = str(dateTimeObj.month)+'.'+ \
            str(dateTimeObj.day)+'.'+ \
            str(dateTimeObj.hour)+'H'+ \
            str(dateTimeObj.minute)+'M'+ \
            str(dateTimeObj.second)+'S'
    return stamp
