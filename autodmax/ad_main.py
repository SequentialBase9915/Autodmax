import sys
import os
import random
import time
from pathlib import Path
from autodmax.ad_functions import *

root = Path(".")
# Initialize the class in ad_data with variables.
var = Loop_state()
trigger = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
# List of trigger values.
# "0" = not triggered and they change to 1 as the macro progresses 

###############################################################################
# Helper functions
###############################################################################

def sound_loop():
    sound_dir = root/'autodmax'/'data'/'ad_shiny_sound.mid'
    sound = str(root.resolve())+'\\'+ str(sound_dir)
    os.system("setvol 100")
    os.system("start " + sound)

def reset_loop():
    if var.reset_no_catch == 0:
        var.reset_counter += 1
        if var.reset_counter > 2:
            var.reset_type_flag = 1
            var.reset_no_catch = 1
            var.ball_saver = 1
        elif var.reset_counter <= 2:
            var.reset_type_flag = 0
        print(f"Executing reset with flag:{var.reset_type_flag}.")
        execute_commands(reset_type[var.reset_type_flag]) 
        print("Execution of reset finished")
    # Reset variables so we re-enter catch loop after doing the no-catch run.
    elif var.reset_no_catch == 1:
        var.reset_counter = 0 
        var.ball_saver = 0
        var.reset_type_flag = 0
    print(f"Reset counter:{var.reset_counter}, Reset Type Flag:{var.reset_type_flag} Reset no catch flag:{var.reset_no_catch}, Ball saver:{var.ball_saver}")
    
def shiny_check(cap):
    check_mons = 0
    progress = [[0,6],[6,11],[11,16],[16,20],[20,50]]
    for level in progress:
        if var.x in range(level[0],level[1]):
            # Exception if we succeed but don't catch boss intentionally.
            if var.x >= 20 and var.ball_saver == 1:
                check_mons = 3
            else:
                check_mons = progress.index(level)
    execute_commands([["A",1],["DD",1],["A",2],])
    shiny_checklist = []
    mon_name = ["First monster","Second Monster","Third Monster","Boss"]
    i = 0
    for i in range(check_mons):
        ret, frame = cap.read()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        shiny_check_value = criteria_match(hsv,shiny_check_area)
        if shiny_check_value[0] > 0:
            shiny_check_value[0] = 1
        now = get_time()
        if i in range(3):
            cv2.imwrite(save_dir+'\\Processed\\shinycheck\\Selection'+str(i)+now+'.PNG',frame)
        elif i == 3:
            cv2.imwrite(save_dir+'\\Selection'+str(i)+now+'.PNG',frame)
        print(mon_name[i], shiny_check_value)
        shiny_checklist.append(shiny_check_value[0])
        i += 1
        execute_commands([["DD",1.3],])                                                                                          
        
    execute_commands([["B",2.2],]) #This needs to stay outside of loop
    if not all( val == 0 for val in shiny_checklist):
        if shiny_checklist.count(1) > 1:
            print("Multiple shinies found",shiny_checklist)
            sys.exit()
        elif len(shiny_checklist) == 4:
            if shiny_checklist[3] == 1:
                print("Shiny boss found", shiny_checklist)
                execute_commands([["DD",1],["DD",1],["DD",1],])
                sound_loop()
                sys.exit()
            else:
                if var.reset_mode == 1:
                    reset_loop()
                if var.reset_mode == 0 or (var.reset_no_catch == 1 and var.reset_counter == 0):
                    var.reset_no_catch = 0
                    print("Shiny regular mon found", shiny_checklist)
                    shiny_pos = shiny_checklist.index(1)
                    if shiny_pos == 1:
                        execute_commands([["DD",1],])
                    elif shiny_pos == 2:
                        execute_commands([["DD",1],["DD",1],])
                    if var.reset_mode == 1:
                        execute_commands(reset_route)
                    execute_commands(return_from_v_with_shiny)                
        else:
            if var.reset_mode == 1:
                reset_loop()
            if var.reset_mode == 0 or (var.reset_no_catch == 1 and var.reset_counter == 0):
                var.reset_no_catch = 0
                print("Shiny regular mon found", shiny_checklist)
                shiny_pos = shiny_checklist.index(1)
                if shiny_pos == 1:
                    execute_commands([["DD",1],])
                elif shiny_pos == 2:
                    execute_commands([["DD",1],["DD",1],])
            execute_commands(return_from_failure_with_shiny)
    else:
        if var.reset_mode == 1:
            reset_loop()
        if var.reset_mode == 0 or (var.reset_no_catch == 1 and var.reset_counter == 0):
            var.reset_no_catch = 0
            print("No shiny found", shiny_checklist)
            if len(shiny_checklist) == 4 or var.reset_mode == 1:
                if var.x in range(20,50):
                    execute_commands(return_from_v_no_shiny)
                else:
                    execute_commands(return_from_failure_no_shiny)
                #This may still fail, needs testing
                
            else:
                execute_commands(return_from_failure_no_shiny)
    print("Debug: Ended shiny check routine")

def criteria_match(hsv,lookup_list):
    
    match_list = []
    
    for element in lookup_list:
        
        selection = hsv[element[0]:element[1],element[2]:element[3]]
        
        mask = cv2.inRange(
            selection,np.asarray(element[4]),np.asarray(element[5])
            )
        
        match_pct = (
            cv2.countNonZero(mask)/(selection.shape[0] * selection.shape[1])
            )*100
        
        match_list.append(match_pct)
        
    return match_list

def dynamax_availability(hsv):
    crest_color = [863,870,1133,1144,[0,0,255],[0,0,255]]
    dynamax_crest = [[crest_color]]
    # Middle white portion when lit up and available
    dynamax_available_check = criteria_match(hsv,dynamax_crest[0])
    dynamax_available = 0
    if all(color_pct > 90 for color_pct in dynamax_available_check):
        dynamax_available = 1
    return dynamax_available

def attack_loop(hsv,cap):
    is_dynamax_available = dynamax_availability(hsv)
    move_choice, move_index = var.player_mon.use_move(var.opponent_mon)
    print("Move chosen is:",move_choice.title())
    if var.first_enc == 0 or var.dmax_reset == 0:
        var.current_pos = 0
        var.dmax_reset = -1
        
    if is_dynamax_available == 1 and move_choice.lower() != "wide guard":
        # Exclusion for wide guard, moved to title
        print("Dynamax used, move choice will be {}".format(move_choice))
        execute_commands([["DL",1],["A",1.3],])
        var.dmax_reset = 3
          
    if var.current_pos == move_index:
        execute_commands([["A",1.3],["A",0.5],["DD",0.5],["A",0.5],])
        # Extra loop in case cursor needs to be shifted.
        if var.dmax_reset > 0:
            var.dmax_reset -= 1
    else:
        difference = (var.current_pos - move_index)
        if difference < 0:
            direction = "DD"
        elif difference > 0:
            direction = "DU"
        for i in range(abs(difference)):
            execute_commands([[direction,0.6],])
        execute_commands([["A",1.3],["A",1.3],["DD",0.5],["A",0.5],])
        # Extra loop in case cursor needs to be shifted
        if var.dmax_reset > 0:
            var.dmax_reset -= 1
    var.current_pos = move_index   

def join_battle():
    execute_commands(join_battle_start+join_battle_mid[var.boss_index]+join_battle_end)
###############################################################################
# Main loop
###############################################################################
def screen_check(hsv,lookups,text,cap):
    global trigger
    
    # Exit loop, resetting globals
    if (var.x+1) > len(trigger):
    # find max value trigger can be and make this reset
        
        print("Finished loop, beginning next.")
        trigger = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        var.first_enc = 0
        var.x = 0
        join_battle()
  
        
    else:
        
        # Ready check screen (for multiplayer only, not currently utilized
        main_matches = criteria_match(hsv,lookups[var.x])
        ret, frame = cap.read()

        ready_check = Img_match(frame,start_screen)
        ready_match = ready_check.match_contours(
            assets_dict["ready_check"],ready_check.get_original_contours()
            )
        
        trade_check = simple_match(
            frame[940:1000,530:675],assets_dict["professor_trade_text"]
            )
        
        item_check = criteria_match(hsv,item_select)
        
        #Main match lookup, of current screen
        if ready_match < 0.01 and var.x == 0 and trigger[var.x] == 0: 
            print(text[var.x], main_matches, var.x)
            print('Ready to go!')
            execute_commands(["A",1])
            trigger[var.x] = 1
            var.x += 1
            
        # Initial Pokemon Selection
        if all(color_pct > 85 for color_pct in main_matches) and var.x == 1 and trigger[var.x] == 0: 
            var.player_mon, var.boss_mon = initial_select_screen(cap)
            trigger[var.x] = 1 
            var.x += 1  

        # Professor action
        elif trade_check > 0.95 and var.x in [2,3,7,8,12,13,17]:
            execute_commands([["B",1],])

        # Item selection screen
        elif item_check[0] > 90 and var.x in [2,3,7,8,12,13,17]:
            item = random.randint(0, 4)
            for r in range(item):
                execute_commands([["DD",0.5],])          
            execute_commands([["A",0.3],])
            print(f"Item {item} selected.")
            time.sleep(7)
            
        # Direction Selection    
        elif all(color_pct > 90 for color_pct in main_matches) and var.x in [2,7,12] and trigger[var.x] == 0:
            print(f"Now at {var.x}")
            if var.x == 2:
                time.sleep(0.5)
                intersections = []
                sleep_timings = [1.2,1,0.9]
                for i in range(3):
                    ret, frame = cap.read()
                    intersections.append(frame)
                    time.sleep(sleep_timings[i])

                junction_1 = [
                    intersections[0][0:1080,500:1000],
                    intersections[0][0:1080,1000:1750]
                    ]
                
                junction_2 = [
                    intersections[1][0:1080,280:655],
                    intersections[1][0:1080,655:1060],
                    intersections[1][0:1080,1060:1500],
                    intersections[1][0:1080,1500:1900]
                    ]
                
                junction_3 = [
                    intersections[2][0:1080,280:655],
                    intersections[2][0:1080,655:1060],
                    intersections[2][0:1080,1060:1500],
                    intersections[2][0:1080,1500:1900]
                    ]
                
                var.choices_1 = [
                    dir_type_match(cleanup_img(part)) for part in junction_1
                    ]
                
                var.choices_2 = [
                    dir_type_match(cleanup_img(part)) for part in junction_2
                    ]
                
                var.choices_3 = [
                    dir_type_match(cleanup_img(part)) for part in junction_3
                    ]
                
                weakness_table_1 = [var.boss_mon.weakness_table.get(choice[0].title()) for choice in var.choices_1]
                weakness_table_2 = [var.boss_mon.weakness_table.get(choice[0].title()) for choice in var.choices_2]
                weakness_table_3 = [var.boss_mon.weakness_table.get(choice[0].title()) for choice in var.choices_3]
                weakness_tables = [weakness_table_1,weakness_table_2,weakness_table_3]
                best_choice_1 = weakness_table_1.index(max(weakness_table_1))
                best_choice_2 = weakness_table_2.index(max(weakness_table_2))
                best_choice_3 = weakness_table_3.index(max(weakness_table_3))               

                
                y_axes = [choice[1] for choice in var.choices_2]
                y_axis_dif = max(y_axes)-min(y_axes)
                print(y_axes, y_axis_dif)
                layouts = [[135,0,"2x2"],[180,1,"2x3"],[65,2,"2x3"]]
                try:
                    current_layout = [item[1:] for item in layouts if abs(item[0]-y_axis_dif)<10][0]
                    path_weighting = []
                    for path in path_layouts[current_layout[0]]:
                        total = 0
                        i = 0
                        for junction in path:
                            total += weakness_tables[i][junction]
                            i += 1
                        path_weighting.append(total)
                    best_path_value = max(path_weighting)
                    best_path = path_layouts[current_layout[0]][path_weighting.index(best_path_value)]
                    var.command_list = command_layouts[current_layout[0]][path_weighting.index(best_path_value)]
                    
                    print("Based on {} layout, best approach would be {} with value of {}. Commands will be {}".format(current_layout[1],best_path,best_path_value,var.command_list))
                    print("Junction 1 choices: {}. Best choice is {}".format(var.choices_1,var.choices_1[best_choice_1]))
                    print("Junction 2 choices: {}. Best choice not considering path is: {}.".format(var.choices_2,best_choice_2))
                    print("Junction 3 choices: {}. Best choice not considering path is: {}.".format(var.choices_3,best_choice_3))
                except:
                    print("Automatic scan failed, using backup route")
                    var.command_list = command_layouts[0][5]
                    print(f"Backup direction is {var.command_list}")

                # Evaluation criteria, will set mode to reset if good path is found and start catching boss.
##                if best_path_value >= 5 and var.reset_mode == 0:
##                    print(var.player_mon.attack_names)
##                    print("Potentially very strong path found, turning on reset mode")
##                    var.ball_saver = 0
##                    var.reset_mode = 1
                        
                time.sleep(5)
                print("'{}' will be executed".format(var.command_list[0]))
                if len(var.command_list[0]) > 1:
                    for command in var.command_list[0]:
                        execute_commands([[command,1],])
                else:
                    execute_commands([[var.command_list[0],1],]) 
                
            elif var.x == 7:
                print("'{}' will be executed".format(var.command_list[1]))
                if len(var.command_list[1]) > 1:
                    for command in var.command_list[1]:
                        execute_commands([[command,1],])
                else:
                    execute_commands([[var.command_list[1],1],])
                
            elif var.x == 12:
                print("'{}' will be executed".format(var.command_list[2]))
                if len(var.command_list[2]) > 1:
                    for command in var.command_list[2]:
                        execute_commands([[command,1],])
                else:
                    execute_commands([[var.command_list[2],1],])
                
                    
            trigger[var.x] = 1
            var.x += 1  

        # Pokemon Exchange Selection
        elif all(color_pct > 90 for color_pct in main_matches) and var.x in [6,11,16] and trigger[var.x] == 0:
            # Look for 0s in the screen move selection and
            # change PP accordingly to evaluate
            zero_match = criteria_match(hsv,zero_check_areas)
            i = 0
            for value in zero_match:
                if value > 2:
                    var.player_mon.attacks[i][4] = 0
                    print("Ran out of attack",i+1)
                i += 1
            var.player_mon = switch_select_screen(cap,var.player_mon)
            var.first_enc = 0
            trigger[var.x] = 1
            var.x += 1
            
        elif (var.x in [3,8,13,17]) and trigger[var.x] == 0:
        # In cases where currently looking for "Battle ready" screen
            catch_check = criteria_match(hsv,catch_screen)
            fainted_check = criteria_match(hsv,fainted)
            failed_check = criteria_match(hsv,final_treasure_screen)
            
            # Run checks for caught, fainted or adventure failed before
            # checking whether we've reached attack screen again.

            # Catch Screen check. Excluding the player status area to make sure
            # this looks at the catch screen.
            # On last catch timer is not visible so exclude this.
            if (catch_check[0] > 90 and catch_check[1] > 90 and catch_check[3] < 10): 
                trigger[var.x] = 1
                trigger[var.x+1] = 1
                trigger[var.x+2] = 1
                var.x += 3
                if var.ball_saver == 1 and var.x == 20:
                    execute_commands([["DD",0.8],["A",0.8],])
                    print("Ball saver mode - ball not used on boss")
                else:
                    execute_commands([["A",0.8],])
                    # Bring up ball selection
                    if var.x != 20:
                        execute_commands([["A",0.8],])
                        # Regular ball (first)
                    else:
                        if var.ball_type == "beast":
                            execute_commands([["DL",0.8],["DL",0.8],["DL",0.8],["DL",0.8],["A",0.8],])
                            # Beast ball (fourth to left)
                        else:
                            execute_commands([["DR",0.8],["A",0.8],])
                            # Premier ball (second)
                pass
                var.first_enc = 0 #reset first encounter counter for next mon
            elif failed_check[0] > 95 and failed_check[1] > 4 and failed_check[0] > 90:
                text_check = catch_screen_check(cap)
                if text_check == True:
            # This triggers if mission failed.
                    print("The adventure failed midway, boss not caught")
                    print("Checking for shinies...")
                    shiny_check(cap)
                    trigger = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] 
                    var.x = 0
                    var.first_enc = 0
                    join_battle()
                elif text_check == False:
                    pass
            elif all(color_pct == 100 for color_pct in fainted_check):
                print(
                    "The main player Pokemon fainted, a button will be pressed \
                    to support and then continue to check for main attack screen"
                    )
                execute_commands([["A",0.3],])
                pass

            elif all(color_pct > 85 for color_pct in main_matches):
                if var.first_enc == 0:
                    execute_commands([["Y",1],["DU",0.8],["A",1.2],])
                    # Added in try, except to get around
                    # last opponent screen update issue
                    try:
                        var.opponent_mon = battle_screen_name(cap)
                    except:
                        var.opponent_mon = var.boss_mon
                    print("Opponent is {}".format(var.opponent_mon.name))
                    execute_commands([["B",1],["B",1],])
                execute_commands([["A",1],["Y",0.7],])
                current_pp = battle_current_pp(cap)
                i = 0
                for attack in var.player_mon.attacks:
                    attack[4] = current_pp[i]
                    i += 1
                var.x += 1
                pass

        elif (var.x in [4,9,14,18]) and trigger[var.x] == 0:
            if all(color_pct > 90 for color_pct in main_matches):
                attack_loop(hsv,cap)
                var.first_enc = 1
                var.x += -1
                
        elif var.x == 20 and trigger[var.x] == 0:
            treasure_check = criteria_match(hsv,final_treasure_screen)
            if treasure_check[0] > 95 and treasure_check[1] > 4 and treasure_check[0] > 90:
                print("Have reached the final selection screen!")
                trigger[var.x] = 1
                
        elif var.x == 20 and trigger[var.x] == 1:
            shiny_check(cap)
            var.x += 1
            var.first_enc = 0
            
        else:
            if all(color_pct > 85 for color_pct in main_matches):
                print("Fell through")
                trigger[var.x] = 1
                var.x += 1    



    
