import pickle
from autodmax.ad_config import ad_settings
from pathlib import Path

root = Path(".")

tables_pickle = root/"autodmax"/"data"/"ad_tables.pickle"
assets_pickle = root/"autodmax"/"data"/"ad_assets.pickle"
###############################################################################
class Loop_state():
    x = 0
    prog = 0
    current_pos = 0
    dmax_reset = 0
    first_enc = 0
    # Flag for whether first attack in enc., used for checking lookup of mon.
    player_mon = None
    boss_mon = None
    opponent_mon = None
    autodynamax_switch = 0
    choices_1 = []
    choices_2 = []
    choices_3 = []
    command_list = []
    reset_mode = ad_settings['reset_mode']
    reset_counter = 0
    # DEFAULT IS 0
    reset_no_catch = 0
    # Reset type flag triggers on > 2.
    # Will need to account for restarts due to hiccup in macro.
    reset_type_flag = 0
    ball_type = ad_settings['ball_type']
    ball_saver = 0
    boss_index = ad_settings['boss_index']

##############################################################################
# Need to be moved to config
##############################################################################
# Boss selection
planned_boss = (ad_settings['boss_dex_num'], 'normal')
# Image save directory
save_dir = ad_settings['save_dir']

##############################################################################
# Assets and tables
##############################################################################
# Assets and tables have been pickled via "asset_pickler.py" and "data_pickler"
# This will be used to re-generate as needed for updates.
def pickle_in(table_name):
    pickle_in = open(table_name,'rb')
    pickle_dict = pickle.load(pickle_in)
    pickle_in.close()
    return pickle_dict

tables_dict = pickle_in(tables_pickle)
df_dex = tables_dict["df_dex"]
df_moves = tables_dict["df_moves"]
df_types = tables_dict["df_types"]

assets_dict = pickle_in(assets_pickle)
# Now using a pickle file for all assets, reference below.
# "dex_nums", "dex_nums_img", "dex_nums_s","dex_nums_img_s",
# "battle_form_list","battle_form_shapes","select_form_list",
# "select_form_shapes","catch_screen_text","professor_trade_text",
# "pp_num_list","pp_num_names", "move_pp_nums",
# "move_pp_values","dir_type_names","dir_type_imgs"

# Dex nums and nums_img (regular and s) are list of dex numbers.
# "nums" generated from filenames, number before file extension separated
# "img" is generated from file contents
# IMPORTANT: There are two sizes of text which need to be distinguished.
# Opponent = large and used in battle screen. Smaller text = init & switch.

# "Battle form" and "Select form" items are list of form names.
# File name split into dex + form and shape names.
# IMPORTANT: Form colors vary between the selection and battle screens.
# Images need to be used separately depending on which screen looked at.
# Professor text used in autodmax main loop.

# "pp_num_list" and "..names" aren't currently being utilized.

###############################################################################
# Data for lookups of elements to inspect with colors
# NOTES: y_l,y_u,x_l,x_u , [color_l], [color_u] formatting.
###############################################################################
sel_lu = [20,100,500,700,[157,148,253],[161,152,255]] # pink

start_screen = [740,800,1345,1685]
#y1,y2,x1,x2

player_select = [
    [10,75,500,600,[157,148,253],[161,152,255]],
    # pink
    [170,190,1000,1040,[0,0,0], [0,0,0]]
    # black, adjusted to avoid dynamax mark
    ] 

initial_dir_select = [
    [49,57,47,64,[0,230,253],[2,234,255]],
    # 4 red hearts
    [49,57,107,124,[0,230,253],[2,234,255]],
    [49,57,167,184,[0,230,253],[2,234,255]],
    [49,57,227,244,[0,230,253],[2,234,255]],
    [326,333,130,250,[0,0,255],[0,0,255]],
    ]

direction_select = [
    [49,59,47,55,[0,230,253],[2,234,255]],
    # red
    [330,370,140,230,[0,0,255],[0,0,255]],
    # white
    [870,880,575,800,[0,0,39],[0,0,43]],
    # grey
    [1040,1070,1440,1540,[0,0,0],[0,0,0]],
    # black
    [1049,1056,1797,1804,[0,0,255],[0,0,255]]
    # white
    ] 

# Below contains health bar info, could be useful in future
battle_ready_OLD = [ 
    [125,134,700,1200,[58,253,231],[62,255,235]],
    # green
    [984,990,140,520,[58,253,231],[62,255,235]],
    # green
    [800,820,1600,1700,[0,0,0],[0,0,0]]
    # black
    ]

battle_ready = [
    [778,780,1768,1775,[171,218,207],[178,255,255]],
    # red
    #[30,45,2,25,[0,0,255],[0,0,255]], # white (currently excluded)
    [962,967,1750,1800,[0,0,255],[0,0,255]],
    # white
    [800,820,1600,1700,[0,0,0],[0,0,0]]
    # black
    ]

attacks_list = [
    [535,575,1907,1918,[0,0,255],[0,0,255]],
    # Y button selection location, white
    [350,400,600,800,[0,0,0],[0,0,0]]
    # black, assumes atk des. is open.
    ]

attack_strength = [
    [580,615,10,1149,[0,0,255],[0,0,255]],
    # white
    [654,740,1851,1858,[0,0,0],[0,0,0]]
    # black
    ]

item_select = [
    [650,750,850,1850,[97,253,253],[101,255,255]]
    # blue
    ]

fainted = [
    [982,995,129,528,[0,0,93],[0,0,99]],
    # grey (two shades)
    [800,820,1600,1750,[0,0,0],[0,0,0]]
    ]

catch_screen = [
    [1016,1031,1543,1548,[0,0,255],[0,0,255]],
    # White, on upper left side of don't catch option
    [904,921,1580,1690,[0,0,0],[0,0,0]],
    # Black area on catch option
    [403,405,1596,1919,[0,0,255],[0,0,255]],
    # white stripe visible on catch screen below timer (except last boss)
    [930,960,20,100,[0,0,255],[0,0,255]]
    # white space that shouldn't be visible on catch screen
    ]

replace_screen = [
    [10,75,500,600,[157,148,253],[161,152,255]],
    [835,870,1100,1150,[0,0,0], [0,0,0]]
    ]
zero_check_areas = [
    [230,265,1745,1855,[0,226,253],[2,230,255]],
    [290,330,1745,1855,[0,226,253],[2,230,255]],
    [355,395,1745,1855,[0,226,253],[2,230,255]],
    [420,460,1745,1855,[0,226,253],[2,230,255]]
    ]

final_treasure_screen = [
    [141,200,2,70,[157,148,253],[161,152,255]],
    # Pink in upper left
    [365,900,1090,1140,[0,0,0],[0,0,0]],
    # Black (to check for arrow)
    [930,938,1200,1280,[154,209,184],[158,215,188]]
    # Dark pink
    # Above a certain point pink shade changes so y remains a small band
    ]

shiny_boss = [
    [560,600,430,480,[150,55,183],[155,64,212]]
    ]

shiny_check_area = [
    [575,625,150,200,[171,212,253],[175,216,255]]
    ]

###############################################################################
# List of lookups for use in main loop
###############################################################################
lookups = [
    [sel_lu],player_select,initial_dir_select,battle_ready,attacks_list,
    catch_screen,replace_screen,direction_select,battle_ready,
    attacks_list,catch_screen,replace_screen,direction_select,battle_ready,
    attacks_list,catch_screen,replace_screen,battle_ready,attacks_list,
    catch_screen,final_treasure_screen
    ] #First list needs extra brackets When multiple checks brackets not needed 
text = ["Selection Screen","Player Selection","Direction selection - Initial",
        "Battle Screen - 1","Attacks List - 1","Catch Screen - 1",
        "Replace Screen - 1","Direction selection - 2","Battle Screen - 2",
        "Attacks List - 2","Catch Screen - 2","Replace Screen - 2",
        "Direction selection - 3","Battle Screen - 3","Attacks List - 3",
        "Catch Screen - 3","Replace Screen - 3","Battle Screen - Boss",
        "Attacks List - Boss","Catch Screen - Boss"
        ]
###############################################################################
# Command lists
###############################################################################

# Command lists for joining/resetting/looping
join_battle_start = [
    ["A",1],["A",1],["A",1.3],["A",0.8],
    ]
    
join_battle_mid = [
    [["A",1.3]], 
    [["A",1.3],["DD",0.5]], 
    [["A",1.3],["DD",0.5],["DD",1]]
    ]

join_battle_end = [
    ["A",1.5],["A",1],["A",4],["DD",1],["A",1.5],
    ]
    
# For above, add in two ["DD",0.5],["DD",1] after ["A",1.3]
# depending on which line monster is on (currently down 1).

reset_normal = [
    ["H",2],["X",1],["A",3.5],["A",1.5],["A",25],["A",12],["A",1.4],["A",1],
    ["A",1],["A",1.2],
    ]

reset_penalty = [
    ["H",2],["X",1],["A",4],["A",1.8],["A",25],["A",12],["A",1.4],["A",1],
    ["A",1],["A",1],["A",1],["A",1],["A",1.2],["A",1.2],
    ]

reset_type = [reset_normal, reset_penalty]
# Used in flag to determine method chosen

return_from_v_no_shiny = [
    ["B",1.3],["A",1],["A",1],["A",1.8],["A",9],["A",0.8],["A",0.8],["A",1.1],
    ["A",0.8],["A",0.8],
    ]

return_from_v_with_shiny = [
    ["A",0.8],["A",0.8],["A",0.5],["A",0.5],["A",1],["A",3],["B",1],["B",9],
    ["A",0.8],["A",0.8],["A",1],["A",0.8],["A",0.8],
    ]

return_from_failure_no_shiny = [
    ["B",1.3],["A",1],["A",1],["A",1.8],["A",9],["A",0.8],["A",0.8],
    ]

return_from_failure_with_shiny = [
    ["A",0.8],["A",0.8],["A",0.5],["A",0.5],["A",1],["A",3],["B",1],["B",9],
    ["A",0.8],["A",0.8],
    ]


###############################################################################
# Path + command lists for each path
###############################################################################

two_by_two_paths = [
    [0,0,0],[0,0,1],[0,1,1],[0,1,2],[0,1,3],
    [1,3,3],[1,3,2],[1,3,1],[1,2,3],[1,2,2],[1,2,1]
    ]

two_by_three_paths = [
    [0,0,0],[0,0,1],[0,0,2],[0,1,0],[0,1,1],[0,1,2],
    [1,3,3],[1,3,2],[1,2,3],[1,2,2],[1,1,0],[1,1,1],[1,1,2]
    ]

three_by_two_paths = [
    [0,0,0],[0,0,1],[0,1,0],[0,1,1],[0,2,0],[0,2,1],
    [1,3,3],[1,3,2],[1,3,1],[1,2,0],[1,2,1]
    ]

two_by_two_commands = [
    ["A","A","A"],
    ["A","A",["DR","A"]],
    ["A",["DR","A"],"A"],
    ["A",["DR","A"],["DR","A"]],
    ["A",["DR","A"],["DR","DR","A"]],
    [["DR","A"],["DR","A"],["DR","DR","A"]],
    [["DR","A"],["DR","A"],["DR","A"]],
    [["DR","A"],["DR","A"],"A"],
    [["DR","A"],"A",["DR","DR","A"]],
    [["DR","A"],"A",["DR","A"]],
    [["DR","A"],"A","A"]
    ]

two_by_three_commands = [
    ["A","A","A"],
    ["A","A",["DR","A"]],
    ["A","A",["DR","DR","A"]],
    ["A",["DR","A"],"A"],
    ["A",["DR","A"],["DR","A"]],
    ["A",["DR","A"],["DR","DR","A"]],
    [["DR","A"],["DR","DR","A"],["DR","A"]],
    [["DR","A"],["DR","DR","A"],"A"],
    [["DR","A"],["DR","A"],["DR","A"]],
    [["DR","A"],["DR","A"],"A"],
    [["DR","A"],"A","A"],
    [["DR","A"],"A",["DR","A"]],
    [["DR","A"],"A",["DR","DR","A"]]
    ]

three_by_two_commands = [
    ["A","A","A"],
    ["A","A",["DR","A"]],
    ["A",["DR","A"],"A"],
    ["A",["DR","A"],["DR","A"]],
    ["A",["DR","DR","A"],"A"],
    ["A",["DR","DR","A"],["DR","A"]],
    [["DR","A"],["DR","A"],["DR","DR","A"]],
    [["DR","A"],["DR","A"],["DR","A"]],
    [["DR","A"],["DR","A"],"A"],
    [["DR","A"],"A","A"],
    [["DR","A"],"A",["DR","A"]]
    ]

path_layouts = [
    two_by_two_paths,two_by_three_paths,three_by_two_paths
    ]

command_layouts = [
    two_by_two_commands,two_by_three_commands,three_by_two_commands
    ]
