from collections import OrderedDict

#flow : 
# - when user click on the upload the tsv loaded tsv will come here.
# - colum number / version for the field will also come from the ui side
# - after clicking on the download button the content mapping will be downloaded in the json format.



def extract_content_mapping(content,version):
 
    values = content.split("\n")
    values = [row.split("\t") for row in values]

    #can be changed if any changes in the GAME JSON - [control/var1/var2/...]
    #should be same across all the sheets.
    LEVEL = 0;
    BOT_PROFILE = 1;
    EARLY_THRESHOLD = 2;
    MID_THRESHOLD = 3;
    EMPTY_CELL_THRESHOLD = 4;
    C_REQ = 5;
    PUZZLE_ID = 6;
    
    if not values:
        return {}
    else:
        level_map = {}
        for row in values[1:]:
            level = row[LEVEL]
            bot_profile = row[BOT_PROFILE]
            early_threshold = float(row[EARLY_THRESHOLD].rstrip('%')) / 100
            mid_threshold = float(row[MID_THRESHOLD].rstrip('%')) / 100
            empty_cell_threshhold = int(row[EMPTY_CELL_THRESHOLD])
            c_req = float(row[C_REQ].rstrip('%')) / 100
            puzzle_id = row[PUZZLE_ID]
           
            level_map[level] = {
                    "pid": puzzle_id,
                    "bc": {
                        "bp" : bot_profile,
                        "cr": c_req,
                        "ect": empty_cell_threshhold,
                        "et": early_threshold,
                        "mt": mid_threshold,
                    }
                }
            
    # Sort levels numerically
    level_map = OrderedDict(sorted(level_map.items(), key=lambda x: float(x[0]) if x[0].replace('.', '', 1).isdigit() else x[0]))
    level_map["v"] = "v" + str(version)
    # Save the content mapping to a JSON file
    return level_map