
## Read ME - Start -
# Right now the program loop over the four different scenarios. 
# It stops the scenario x if there is no equilibrium after 300 iterations
# In the case you want to run the four scenario just press ctrl + alt + R (PS: don't forget to uncomment section ##Package installation if you run it for the first time )
# In the case you want to run one particular scenario (and not the four at one): See section ##scenario

## Parameters that can be modify if relevant:
#qo = located in this script ##External values 
#afe = located in this script ##External values 
## Read ME - End

## V14 (Sept 2026) - changes relative to V13R1, all marked "V14:" in the code
##  1. Border-charge values come from 0_External_data/DeDuCE_rework/tms_f_initial_shocks_DeDuCE.xlsx,
##     sheet tmsf_sheet (default AVE_pha400 = 400 $/ha of embodied deforestation), instead of tms_f_initial_shocks.xlsx
##  2. The charge applies to every column of that sheet (17 sectors: the nine of V13 + rmk, wol, ruminantmeat,
##     dairy, vegoil, lea, pdr, c_b) through list_commodity_tmsf; list_commodity (qes/qo/qxw commitments) is unchanged
##  3. Iteration 0 (EU alone charging the twelve producers) is solved by the script with the new values;
##     V13 read it from 2_Model/BU/NATDEF.sl4, which was solved with the old values written in BU/NATDEF.cmf
##  4. Outputs go to 3_Output/<approach>/<parameter>_<run_tag>/<scenario>/ and 4_DB/..._<run_tag>.csv,
##     so the V13 results are not overwritten
##  Everything else (qes/afeall member commitment, flat mean penalty on non-producer outsiders, thresholds) is unchanged.

## Package installation, 
## Run these lines only once to install the packages (do this only one time)
#install.packages('devtools')
#devtools::install_git('https://github.com/USDA-ERS/MTED-HARr.git')
#install.packages("readxl")
#install.packages("xlsx", dependencies=TRUE)
#install.packages("rJava")
#install.packages("xlsx")

#clear the environment
rm(list = ls())

## Run these lines in each new R session where you need these packages
library(devtools)
library(xlsx)
require(HARr)
library("readxl")
library("rstudioapi")
library(dplyr)
library(writexl)
library(tidyr)

script_path <- getSourceEditorContext()$path 
script_folder <- dirname(script_path)
parent_folder <- dirname(script_folder)
GTAPAEZ_path <- file.path(parent_folder, "2_Model/")
external_data_path <- file.path(parent_folder, "0_External_data/")

setwd(GTAPAEZ_path)

##External values 
#Values qo to stop the deforestation based on HILDA+ V2_1 calculation
# Function to process a sheet and create a list of named vectors

# Import the data
data_qo <- read_excel(paste0(external_data_path, "/qo_values.xlsx"))
## V14: border charge = DeDuCE-based table, one sheet per price scenario
tmsf_sheet <- "AVE_pha400"    # AVE_pha400 | AVE_pha2000 | AVE_pha10000 | AVE_co2_50 | AVE_co2_100 | AVE_co2_190
run_tag    <- sub("^AVE_", "", tmsf_sheet)   # "pha400": suffix of the output folders and csv files
data_tmsf  <- read_excel(paste0(external_data_path, "/DeDuCE_rework/tms_f_initial_shocks_DeDuCE.xlsx"), sheet = tmsf_sheet)
names(data_tmsf) <- tolower(names(data_tmsf))   # HARr lower-cases set elements ("RuminantMeat" -> "ruminantmeat")
data_qxw <- read_excel(paste0(external_data_path, "/qxw_values.xlsx"))
limit <- read_excel(paste0(external_data_path,"/GDP_values.xlsx"))
limit$GDP <- -0.001 * limit$GDP

# Function to process data
process_data <- function(data) {
  country_names <- data[[1]]
  attributes <- data[-1]
  setNames(lapply(seq_len(nrow(attributes)), function(i) setNames(unlist(attributes[i, ]), names(attributes))), country_names)
}

process_sheet <- function(sheet_name) {
  # Import the data
  data <- read_excel(paste0(external_data_path, "/qes_values.xlsx"), sheet = sheet_name, col_names = TRUE, col_types = NULL, na = "", skip = 0)
  # Extract country names
  country_names <- data[[1]]
  # Remove the country names column to keep only the attributes
  attributes <- data[-1]
  # Initialize an empty list to store the country data
  shock_values <- list()
  # Loop through each row and create a named vector for each country
  for (i in 1:nrow(attributes)) {
    # Extract the row as a named vector
    country_data <- unlist(attributes[i, ])
    names(country_data) <- names(attributes)
    # Assign it to the list with the country name
    shock_values[[country_names[i]]] <- country_data
  }
  return(shock_values)
}

# Loop to process each AEZ and create separate variables
for (i in 1:18) {
  sheet_name <- paste0("AEZ", i)
  variable_name <- paste0("shock_value_aez_", i)
  assign(variable_name, process_sheet(sheet_name))
}

# Apply the function to both datasets
shock_values_qo <- process_data(data_qo)
shock_values_tmsf <- process_data(data_tmsf)
shock_values_qxw <- process_data(data_qxw)

## Parameters
## List of regions used in this simulation
sets = read_har('sets.har')
region_sets = sets["reg"]
df_r <- data.frame(region_sets)
# convert the regions used into the simulation as a vector
region_sets <- unlist(df_r)
list_producer_countries <- c("angola", "argentina", "bolivia", "brasil", 
                             "colombia","ghana","ivorycoast",
                             "indonesia","malasya","paraguay","peru","drc")

list_non_producer_countries <- c("madagascar","mozambique","myanmar", "nigeria", "uruguay","venezuela",
                                 "newzealand","oceania","china","india","japan","korea","eastasia",
                                 "seasia","southasia","us","canada", "mexico","latinamer","eu27",
                                 "uk","russia","efta","mena","nafr","wafr","cafr","eafr","safr","restofworld")

list_commodity <- c("sgr", "ruminant", "gro", "ocr", 
                    "osd","pcr","pfb",
                    "v_f","wht")

## V14: sectors that carry the border charge = every column of the tms_f sheet (17 sectors).
## To charge only the nine sectors of V13:  list_commodity_tmsf <- list_commodity
list_commodity_tmsf <- names(data_tmsf)[-1]

original_ev_new <- read_excel(paste0(external_data_path,"/Original_EV.xlsx"),sheet=1,col_names= FALSE,col_types=NULL,na="",skip= 0)

# Find the parameter to play with 
# qo, qoes or qxw
#list_parameter <- c("qes")
list_parameter <- c("qo", "qes", "qxw")

## Scenarios
# Un-comment the line below and comment the line above to run one single scenario
scenarios <- c("Scenario_D")

#list_approach <- c("Realistic_wi_china","Realistic_wo_china","Diplomatic","Idealist")
list_approach <- c("Realistic_wi_china","Diplomatic","Realistic_wo_china","Idealist")
#list_approach <- c("Diplomatic")

## Reset from the previous calculation
# Loop to iterate through each BU file

# List of BU files to copy
bu_files <- c("NATDEF.har", "NATDEF.sl4", "gdata.upd", "NATDEF.cmf")

# Source and destination folders are as per your setup
source_folder_copy <- file.path(parent_folder, "2_Model", "BU/")
destination_folder_paste <- GTAPAEZ_path
for (bu_file in bu_files) {
  
  # Full path of the source and destination files
  source_file_path_copy <- file.path(source_folder_copy, bu_file)
  destination_file_path_paste <- file.path(destination_folder_paste, bu_file)
  
  # Check if the source file exists
  if (!file.exists(source_file_path_copy)) {
    print(paste("Source file does not exist:", bu_file))
    next
  }
  
  # Check if the destination folder exists
  if (!dir.exists(destination_folder_paste)) {
    print("Destination folder does not exist.")
    next
  }
  
  # Attempt to copy and overwrite if the file already exists
  result <- file.copy(source_file_path_copy, destination_file_path_paste, overwrite = TRUE)
  
  # Check the result
  if (result) {
    print(paste("File copy successful for", bu_file))
  } else {
    print(paste("File copy failed for", bu_file))
  }
}

run_Gtap <- function(iter){
  #' Run the GEMPACK simulation and return the 
  #' @iter indicates the iteration number but is not included into the calculation
  #' Run the GEMPACK executable, read the EV results from the SL4 output of the simulation  
  #' and return the EV as a numeric vector of x values (x: number of countries into the simulation)
  
  # Load the necessary library
  tryCatch({
    library(HARr)
  }, error = function(e) {
    stop("HARr package could not be loaded: ", e)
  })
  
  # Run the executable with the system2 function
  system2("GTAPV7-AEZ.exe", c("-cmf", "NATDEF.CMF"))
  
  # Read data and extract relevant parts
  data = read_SL4('NATDEF.sl4')
  equivalent_variation = data["ev"]
  df <- data.frame(equivalent_variation)
  values_EV <- unlist(df)
  values_EV <- as.numeric(values_EV)
  
  # Return the vector
  return(values_EV)
}

forest_data <- function(iter){
  #' Run the GEMPACK simulation and return the 
  #' @iter indicates the iteration number but is not included into the calculation
  #' Run the GEMPACK executable, read the EV results from the SL4 output of the simulation  
  #' and return the EV as a numeric vector of x values (x: number of countries into the simulation)

  # Read data and extract relevant parts
  data = read_SL4('NATDEF.sl4')
  luc_variation = data[["del_luc"]][,'forestland',,]*1000
  df <- data.frame(luc_variation)
  
  row_indices <- rep(rownames(df),times =ncol(df))
  col_indices <- rep(colnames(df), each =nrow(df))
  
  
  unpivoted_df <- data.frame(
    col = row_indices,
    row = col_indices,
    value = as.vector(as.matrix(df))
  )
  
  luc <- unpivoted_df %>%
    pivot_wider(names_from = col, values_from = value)
  
  # Return the vector
  return(luc)
}

init_region <- function(iter){
  #' Run the GEMPACK simulation and return the 
  #' @iter indicates the iteration number but is not included into the calculation
  #' Run the GEMPACK executable, read the EV results from the SL4 output of the simulation  
  #' and return the EV as a numeric vector of x values (x: number of countries into the simulation)
  
  # Load the necessary library
  tryCatch({
    library(HARr)
  }, error = function(e) {
    stop("HARr package could not be loaded: ", e)
  })
  
  # Read data and extract relevant parts
  data = read_SL4('NATDEF.sl4')
  equivalent_variation = data["ev"]
  df <- data.frame(equivalent_variation)
  values_EV <- unlist(df)
  values_EV <- as.numeric(values_EV)
  
  # Return the vector
  return(values_EV)
}

selection_region <- function(prvs_values_EV, values_EV, region_sets, iter){
  #' Select the region names that have a EV<0 
  #' @iter indicates the iteration number but is not included into the calculation
  #' Run the GEMPACK executable, read the EV results from the SL4 output of the simulation  
  #' and return the EV as a numeric vector of x values (x: number of countries into the simulation)
  
  output_table = cbind(region_sets, prvs_values_EV, values_EV, iter)
  
  df_3 <- data.frame(output_table)
  df_3$prvs_values_EV <- as.numeric(df_3$prvs_values_EV)
  df_3$values_EV <- as.numeric(df_3$values_EV)
  
  df_4 <- df_3[df_3$values_EV > df_3$prvs_values_EV , ]
  df_4 <- subset(df_4, select = -prvs_values_EV)
  region_positiv_EV <- df_4[[1]]
  l = iter-1
  # Write the vector to a file. Include the iteration number in the file name.
  write.table(output_table, file = paste0(save_path, "Equivalent_Variation_round_", l, ".txt"), row.names = FALSE, col.names = FALSE)
  
  # Return the vector
  return(region_positiv_EV)  
}

move_producer_coalition <- function(iter_region) {
  producer_coalition <- intersect(iter_region, list_producer_countries)
  iter_region <- setdiff(iter_region, producer_coalition)
  return(list(iter_region = iter_region, producer_coalition = producer_coalition))
}

move_producer_reset <- function(reset_region) {
  producer_reset <- intersect(reset_region, list_producer_countries)
  reset_region <- setdiff(reset_region, producer_reset)
  return(list(reset_region = reset_region, producer_reset = producer_reset))
}

shock_eu27<- function(shock, outside_producer, outside_non_producer) {
  for(producer in outside_producer) {
    for(commodity in list_commodity_tmsf) {   # V14
      shock[["0101"]][commodity, producer, "eu27"] <- shock_values_tmsf[[producer]][commodity]
    }
  }
  for(non_producer in outside_non_producer) {
    for(commodity in list_commodity_tmsf) {   # V14
      shock[["0101"]][commodity,non_producer,"eu27"] <- mean(data_tmsf[[commodity]])
    }
  }
  
  return(shock)
}

shock_eu27_exp<- function(shock, inside_producer, inside_non_producer) {
  for(commodity in list_commodity_tmsf) {   # V14
    for(producer in inside_producer) {
      shock[["0101"]][commodity, "eu27", producer] <- 0.0
    }
    for(non_producer in inside_non_producer) {
      shock[["0101"]][commodity, "eu27", non_producer] <- 0.0
    }
  }
  
  return(shock)
}

shock_ABCD <- function(shock, club_non_producer, outside_producer) {
  for(club in club_non_producer) {
    for(producer in outside_producer) {
      for(commodity in list_commodity_tmsf) {   # V14
        shock[["0101"]][commodity, producer, club] <- shock_values_tmsf[[producer]][commodity]
      }
    }
  }
  return(shock)
}

shock_BD <- function(shock, club_non_producer, outside_non_producer) {
  for(club in club_non_producer) {
    for(non_producer in outside_non_producer) {
      for(commodity in list_commodity_tmsf) {   # V14
        shock[["0101"]][commodity,non_producer, club] <- mean(data_tmsf[[commodity]])
      }
    }
  }
  return(shock)
}

shock_D <- function(shock, club_producer, outside_non_producer) {
  for(club in club_producer) {
    for(non_producer in outside_non_producer) {
      for(commodity in list_commodity_tmsf) {   # V14
        shock[["0101"]][commodity,non_producer, club] <- mean(data_tmsf[[commodity]])
      }
    }
  }
  return(shock)
}

shock_CD <- function(shock, club_producer, outside_producer) {
  for(club in club_producer) {
    for(producer in outside_producer) {
      for(commodity in list_commodity_tmsf) {   # V14
        shock[["0101"]][commodity, producer, club] <- shock_values_tmsf[[producer]][commodity]
      }
    }
  }
  return(shock)
}

# Function to update the .cmf file
update_cmf_file <- function(new_text,i) {
  # Read the file
  cmf_path <- paste0(GTAPAEZ_path,"/NATDEF.cmf")
  
  lines <- readLines(cmf_path, warn = FALSE)
  # Find the line number for "Rest Endogenous;"
  cutoff_line <- which(lines == "! Part for productivity shocks from R;")
  # Check if the line was found
  if (length(cutoff_line) == 0) {
    stop("The line 'Rest Endogenous ;' was not found in the file.")
  }
  # Keep all lines up to and including "Rest Endogenous;"
  lines <- lines[1:cutoff_line]
  
  # Append new text
  lines <- c(lines, new_text)
  # Write the updated content back to the file
  writeLines(lines, cmf_path)
  
  filename = paste0(save_path,"CMF_iter_", i, ".cmf")
  # Modify lines to remove " and \
  cleaned_lines = gsub('"', '', lines)  # Remove double quotes
  cleaned_lines = gsub('\\\\', '', cleaned_lines)  # Remove backslashes, note double escape to represent a single backslash
  # Write to file without quotes and backslashes
  write.table(cleaned_lines, filename, sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE)
  
}

# Function to generate text for each country
generate_swap_for_qo <- function(country) {
  swap_qo <- c()  # Create an empty vector to store results
  
  for(commodity in list_commodity) {
    line <- paste("swap qo(\"", commodity, "\",\"", country, "\") = aoall(\"", commodity, "\",\"", country, "\");", sep = "")
    swap_qo <- c(swap_qo, line)  # Append the generated string to the results
  }
  
  return(swap_qo)
}

generate_shock_for_qo <- function(club_producer) {
  results_qo <- c()  # Create an empty vector to store results
  
  for(producer in club_producer) {
    for(commodity in list_commodity) {
      value <- shock_values_qo[[producer]][commodity] 
      line <- paste("Shock qo(\"", commodity, "\",\"", producer, "\") = ", value, ";", sep = "")
      results_qo <- c(results_qo, line)  # Append the generated string to the results
    }
  }
  
  return(results_qo)
}

generate_text_for_qxw <- function(club_producer) {
  results_qxw <- c()  # Create an empty vector to store results
  
  for(producer in club_producer) {
    for(commodity in list_commodity) {
      value <- shock_values_qxw[[producer]][commodity]
      if (value < 0) {
      line_shock <- paste("Shock qxw(\"", commodity, "\",\"", producer, "\") = ", value, ";", sep = "")
      line_swap <- paste("swap qxw(\"", commodity, "\",\"", producer, "\")=tmf_f(\"", commodity, "\",\"", producer, "\");", sep = "")
      results_qxw <- c(results_qxw, line_swap, line_shock)  # Append the generated string to the results
      }
    }
  }
  
  return(results_qxw)
}

# generate_text_for_qoes <- function(club_producer) {
#   results_qoes <- c()  # Create an empty vector to store results
#   for(producer in club_producer) {
#     for(commodity in list_commodity) {
#       for (i in 1:18) {
#         shock_index <- paste0("aez", i)
#         shock_value_var_name <- paste0("shock_value_aez_", i)
#         shock_value_var <- get(shock_value_var_name)
#         value <- shock_value_var[[producer]][[commodity]]
#         
#         if (value < 0) {
#           line_shock <- paste("Shock qoes(\"", shock_index, "\", \"", commodity, "\",\"", producer, "\")=", value, ";", sep = "")
#           line_swap <- paste("swap qoes(\"", shock_index, "\", \"", commodity, "\", \"", producer, "\")=afeall(\"", shock_index, "\", \"", commodity, "\", \"", producer, "\");", sep = "")
#           results_qoes <- c(results_qoes, line_swap, line_shock)
#         }  # Append the generated string to the results
#       }
#     }
#   }
#   
#   return(results_qoes)
# }

generate_text_for_qes <- function(club_producer) {
  results_qes <- character(0)  # empty character vector
  
  for (producer in club_producer) {
    for (commodity in list_commodity) {
      for (i in 1:18) {
        # AEZ1..AEZ18 (no zero padding)
        shock_index <- sprintf("AEZ%d", i)
        
        shock_value_var_name <- sprintf("shock_value_aez_%d", i)
        shock_value_var <- get(shock_value_var_name, inherits = TRUE)
        value <- shock_value_var[[producer]][[commodity]]
        
        if (is.finite(value) && value < 0) {
          line_swap <- sprintf(
            'swap qes("%s","%s","%s")=afeall("%s","%s","%s");',
            shock_index, commodity, producer,
            shock_index, commodity, producer
          )
          line_shock <- sprintf(
            'shock qes("%s","%s","%s") = %s;',
            shock_index, commodity, producer,
            format(value, scientific = FALSE, digits = 16)
          )
          results_qes <- c(results_qes, line_swap, line_shock)
        }
      }
    }
  }
  
  results_qes
}

for (parameter in list_parameter){
  
  for (approach in list_approach){
  
    for(scenario in scenarios) {
    
    save_path <- file.path(parent_folder, "3_Output",approach, paste0(parameter, "_", run_tag),scenario,"/")   # V14
    dir.create(save_path, recursive = TRUE, showWarnings = FALSE)                                              # V14
    # Store the original shock data
    original_shock = read_har('NATDEF.har')

# Initialize an empty list to hold the outputs
    
outputs <- list()
area <- list()

iter_area <- list()
iter_area_producer <- list()
iter_area_wo_producer <- list()
reset_area <- list()
reset_area_producer <- list()
reset_area_wo_producer <- list()

iter_region <- list()
iter_region_producer <- list()
iter_region_wo_producer <- list()
reset_region <- list()
reset_region_producer <- list()
reset_region_wo_producer <- list()

# Get the initial output
## V14: iteration 0 = the EU alone charging the twelve producers with the NEW values.
## V13 took it from BU/NATDEF.sl4, solved with the old "shock tms(...)" lines of BU/NATDEF.cmf.
shock <- read_har('NATDEF.har')
shock[["0101"]][] <- 0
shock <- shock_eu27(shock, list_producer_countries, character(0))   # producers -> eu27 only, no member yet
write_har(shock, 'NATDEF.har', maxSize = 1e4)
cmf_path <- paste0(GTAPAEZ_path,"/NATDEF.cmf")
lines <- readLines(cmf_path, warn = FALSE)
lines <- c(lines[1:which(lines == "! Part for productivity shocks;")],
           'Shock tms_f =  file NATDEF.har header "0101";', '! Part for productivity shocks from R;')
writeLines(lines, cmf_path)
outputs[[1]] <- run_Gtap(1)
thresholds <- read_excel(paste0(external_data_path,"/",approach,"/Thresholds_GTAPAEZ_Game_theory.xlsx"),sheet=2,col_names= FALSE,col_types=NULL,na="",skip= 0)
thresholds_down <- thresholds[, c(3)]
thresholds <- thresholds[, c(2)]

i <- 1
sign_check <- FALSE

while (!sign_check){
  # Get the output from the new run
  shock = read_har('NATDEF.har')
  cmf <- "NATDEF.cmf"
  if (i == 1){
    # Combine data, convert to data frame, and change column to numeric
    df <- data.frame(region_sets, V2 = as.numeric(outputs[[i]]), i, t = as.numeric(thresholds_down[[i]]))
    # Filter rows where V2 is greater than 0 and extract the first column
    area[[i]] <- df[(df$V2 > 0) | (df$V2 < 0 & abs(df$V2) < df$t) , "region_sets"]
    # Write the output_table_wrt to a file
    write.table(cbind(region_sets, outputs[[i]], original_ev_new, i), file = paste0(save_path, "Equivalent_Variation_round_0", ".txt"), row.names = FALSE, col.names = FALSE)
  }else {
    area[[i]] <- selection_region(outputs[[i-1]], outputs[[i]], region_sets , i)
  }
  
  for (r in 1:42) {
    # Check if this region had a negative output in the previous iteration
    if (i == 1 ) {
      iter_area[[i]] <- setNames(area[[i]], paste0("h", seq_along(area[[i]])))
      reset_area[[i]] <- setNames(setdiff(region_sets, unlist(iter_area[[i]])), paste0("h", seq_along(setdiff(region_sets, unlist(iter_area[[i]])))))
      
      #Switch for the first iteration
      temp <- iter_area[[i]]
      iter_area[[i]] <- reset_area[[i]]
      reset_area[[i]] <- temp
      iter_region <- iter_area[[i]]
      reset_region <- reset_area[[i]]
      move <- move_producer_coalition(iter_region)
      iter_area_wo_producer[[i]] <- move$iter_region
      iter_area_producer[[i]]    <- move$producer_coalition
      iter_region_wo_producer  <- iter_area_wo_producer[[i]]
      iter_region_producer <- iter_area_producer[[i]]
      move_reset <- move_producer_reset (reset_region)
      reset_area_wo_producer[[i]] <- move_reset$reset_region
      reset_area_producer[[i]] <- move_reset$producer_reset
      reset_region_wo_producer <- reset_area_wo_producer[[i]]
      reset_region_producer <- reset_area_producer[[i]]
    }else if (i == 2) {
      if ((region_sets[[r]] %in% reset_area[[i - 1]] == TRUE && (outputs[[i]][r] > outputs[[i - 1]][r])) ||
          (region_sets[[r]] %in% reset_area[[i - 1]] == TRUE && (outputs[[i]][r] < outputs[[i - 1]][r]) && abs((outputs[[i]][r] - outputs[[i - 1]][r]))<thresholds_down[[1]][r]) ||
          (region_sets[[r]] %in% iter_area[[i - 1]]  == TRUE && (outputs[[i]][r] < outputs[[i - 1]][r]) && abs((outputs[[i]][r] - outputs[[i - 1]][r]))>thresholds[[1]][r])) 
      {
        # The output was negative in the previous iteration and is positive now
        # Add the region to the switched_regions list
        reset_region <- c(reset_region, region_sets[r])
        reset_area[[i]] <- reset_region
        reset_region <- unlist(reset_region)
        move_reset <- move_producer_reset (reset_region)
        reset_area_wo_producer[[i]] <- move_reset$reset_region
        reset_area_producer[[i]] <- move_reset$producer_reset
        reset_region_wo_producer <- reset_area_wo_producer[[i]]
        reset_region_producer <- reset_area_producer[[i]]
      }else {
        iter_region <- c(iter_region, region_sets[r])
        iter_area[[i]] <- iter_region
        iter_region <- unlist(iter_region)
        move_producer <- move_producer_coalition(iter_region)
        iter_area_wo_producer[[i]] <- move_producer$iter_region
        iter_area_producer[[i]] <- move_producer$producer_coalition
        iter_region_wo_producer <- iter_area_wo_producer[[i]] 
        iter_region_producer <- iter_area_producer[[i]]
      }
    }else {
      if ((region_sets[[r]] %in% reset_area[[i - 1]] == TRUE && (outputs[[i]][r] > outputs[[i - 1]][r])) ||
          (region_sets[[r]] %in% reset_area[[i - 1]] == TRUE && (outputs[[i]][r] < outputs[[i - 1]][r]) && abs((outputs[[i]][r] - outputs[[i - 1]][r]))<thresholds_down[[1]][r]) ||
          (region_sets[[r]] %in% iter_area[[i - 1]]  == TRUE && (outputs[[i]][r] < outputs[[i - 1]][r]) && abs((outputs[[i]][r] - outputs[[i - 1]][r]))>thresholds[[1]][r]) ||
          (region_sets[[r]] %in% iter_area[[i - 1]]  == TRUE && (outputs[[i]][r] < limit$GDP[r]) && (outputs[[i - 1]][r] < limit$GDP[r]) && (outputs[[i - 2]][r] < limit$GDP[r]))) 
      {
        # The output was negative in the previous iteration and is positive now
        # Add the region to the switched_regions list
        reset_region <- c(reset_region, region_sets[r])
        reset_area[[i]] <- reset_region
        reset_region <- unlist(reset_region)
        move_reset <- move_producer_reset (reset_region)
        reset_area_wo_producer[[i]] <- move_reset$reset_region
        reset_area_producer[[i]] <- move_reset$producer_reset
        reset_region_wo_producer <- reset_area_wo_producer[[i]]
        reset_region_producer <- reset_area_producer[[i]]
      }else {
        iter_region <- c(iter_region, region_sets[r])
        iter_area[[i]] <- iter_region
        iter_region <- unlist(iter_region)
        move_producer <- move_producer_coalition(iter_region)
        iter_area_wo_producer[[i]] <- move_producer$iter_region
        iter_area_producer[[i]] <- move_producer$producer_coalition
        iter_region_wo_producer <- iter_area_wo_producer[[i]] 
        iter_region_producer <- iter_area_producer[[i]]
      }
    } 
  }

  shock[["0101"]] <- original_shock[["0101"]]
  
  shock <- shock_ABCD(shock, iter_area_wo_producer[[i]], reset_area_producer[[i]])
  shock <- shock_eu27(shock, reset_area_producer[[i]], reset_area_wo_producer[[i]])
  shock <- shock_BD(shock, iter_area_wo_producer[[i]], reset_area_wo_producer[[i]] )
  shock <- shock_D(shock, iter_area_producer[[i]],reset_area_wo_producer[[i]])
  shock <- shock_CD(shock, iter_area_producer[[i]],reset_area_producer[[i]])
  shock <- shock_eu27_exp(shock, iter_area_producer[[i]],iter_area_wo_producer[[i]])

  cmf_path <- paste0(GTAPAEZ_path,"/NATDEF.cmf")
  lines <- readLines(cmf_path, warn = FALSE)
  cutoff_line <- which(lines == "! Part for productivity shocks;")
  if (length(cutoff_line) == 0) {
    stop("The line 'Rest Endogenous ;' was not found in the file.")
  }
  # Keep all lines up to and including "Rest Endogenous;"
  lines <- lines[1:cutoff_line]
  lines_tms_f <- 'Shock tms_f =  file NATDEF.har header "0101";'
  lines_tms_f_2 <- '! Part for productivity shocks from R;'
  lines <- c(lines,lines_tms_f, lines_tms_f_2)
  # Write the updated content back to the file
  writeLines(lines, cmf_path)
  
  filename = paste0(save_path,"CMF_iter_", i, ".cmf")
  # Modify lines to remove " and \
  cleaned_lines = gsub('"', '', lines)  # Remove double quotes
  cleaned_lines = gsub('\\\\', '', cleaned_lines)  # Remove backslashes, note double escape to represent a single backslash
  # Write to file without quotes and backslashes
  write.table(cleaned_lines, filename, sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE)

  
  if(parameter == "qo"){
    
    cmf_path <- paste0(GTAPAEZ_path,"/NATDEF.cmf")
    lines <- readLines(cmf_path, warn = FALSE)
    
    method_line_index <- grep("Method =", lines)
    step_line_index <- grep("Steps =", lines)
    subinterval_line_index <- grep("subintervals =", lines)
    accuracy_line_index <- grep("automatic accuracy =", lines)
    
    lines[method_line_index] <- "Method = Euler;"
    lines[step_line_index] <- "Steps = 2 4;"
    lines[subinterval_line_index] <- "subintervals = 3;"
    lines[accuracy_line_index] <- "automatic accuracy = no;"
    
    writeLines(lines, cmf_path)}
  
  # if(parameter == "qxw"){
  #   
  #   cmf_path <- paste0(GTAPAEZ_path,"/NATDEF.cmf")
  #   lines <- readLines(cmf_path, warn = FALSE)
  #   
  #   method_line_index <- grep("Method =", lines)
  #   step_line_index <- grep("Steps =", lines)
  #   subinterval_line_index <- grep("subinterval =", lines)
  #   accuracy_line_index <- grep("automatic accuracy =", lines)
  #   
  #   lines[method_line_index] <- "Method = Euler;"
  #   lines[step_line_index] <- "Steps = 1 2;"
  #   lines[subinterval_line_index] <- "subinterval = 3;"
  #   lines[accuracy_line_index] <- "automatic accuracy = no;"
  #   
  #   writeLines(lines, cmf_path)}
  

  # Generate productivity shock
    text_q <- generate_shock_for_qo(iter_area_producer[[i]])
    # Generate productivity swap
    text_for_all_countries <- sapply(iter_area_producer[[i]], generate_swap_for_qo)
    # Flatten text_for_all_countries if it's not already a vector
    flattened_text_for_all_countries <- as.vector(text_for_all_countries)
    
    # Combine flattened_text_for_all_countries and text_q into one vector
    # Append the additional lines
    #additional_lines_1 <- "Shock tms_f = file TMSF.har header \"0083\";"
    #combined_text <- c(flattened_text_for_all_countries, text_q, additional_lines_1)
    
    text_qes <- generate_text_for_qes(iter_area_producer[[i]])

    
    #text_qoes_for_all_countries <- sapply(iter_area_producer[[i]], generate_swap_for_qoes)
    # Flatten text_for_all_countries if it's not already a vector
    #flattened_text_qoes_for_all_countries <- as.vector(text_qoes_for_all_countries)'
    text_qxw <- generate_text_for_qxw(iter_area_producer[[i]])
    
    if (parameter == "qo"){
      combined_text <- c(flattened_text_for_all_countries, text_q)
      } else if(parameter == "qes") {combined_text <-text_qes
        } else {combined_text <-text_qxw}
    
    if (length(combined_text) > 0) {
      update_cmf_file(combined_text,i)
    }

  
  tmsf <- list("0101" = shock[["0101"]])
  
  # write the different shocks
  #write_har(tmsf, "TMSF.har" , maxSize = 1e4)
  write_har(shock, 'NATDEF.har', maxSize = 1e4)
  
  # write the iteration for control
  #filename_2 = paste0(save_path,"tmsf_iter_", i, ".har")
  #write_har(tmsf, filename_2 , maxSize = 1e4)

  l = i-1
  
  filename_3 = paste0(save_path,"NATDEF_iter_", i, ".har")
  write_har(shock, filename_3 , maxSize = 1e4)
  
# Write the vector to a file. Include the iteration number in the file name.
  
  luc <- forest_data(i)
  
  write.table(luc, file = paste0(save_path,"Forest_LU_Region_Ha_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  
  write.table(reset_region, file = paste0(save_path,"Reset_Region_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(iter_region, file = paste0(save_path,"Iter_Region_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(iter_region_wo_producer, file = paste0(save_path,"Iter_Region_wo_producer_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(iter_region_producer, file = paste0(save_path, "Iter_Region_producer_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(reset_region_wo_producer, file = paste0(save_path, "Reset_Region_wo_producer_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(reset_region_producer, file = paste0(save_path, "Reset_Region_producer_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  
  outputs[[i + 1]] <- run_Gtap(i + 1)
  
  # if (4<i && i<25){
  #   # Calculate the difference measure between the current output and the previous one
  #   # For example, you can use the sum of absolute differences. Depending on your needs, you might want to use a different measure.
  #   #sign_check <- all(outputs[[i + 1]] > outputs[[i]] | outputs[[i + 1]] > outputs[[1]])
  #   
  #   #sign_check <- length(setdiff(iter_area[i], iter_area[i-1])) == 0
  #   #comparing with the last 4 iterations 
  #     for (j in 1:3) {
  #       if ((length(setdiff(iter_area[[i]], iter_area[[i - j]])) == 0) && (length(setdiff(iter_area[[i-j]], iter_area[[i]])) == 0)) {
  #         sign_check <- TRUE
  #         break  # Exit the loop if a match is found
  #       }
  #     }
  # }
  
  if (2<i && i<24){
    # Calculate the difference measure between the current output and the previous one
    # For example, you can use the sum of absolute differences. Depending on your needs, you might want to use a different measure.
    #sign_check <- all(outputs[[i + 1]] > outputs[[i]] | outputs[[i + 1]] > outputs[[1]])
    
    #sign_check <- length(setdiff(iter_area[i], iter_area[i-1])) == 0
    #comparing with the last 4 iterations 
      if ((length(setdiff(iter_area[[i]], iter_area[[i - 1]])) == 0) && (length(setdiff(iter_area[[i-1]], iter_area[[i]])) == 0)) {
        sign_check <- TRUE
        break  # Exit the loop if a match is found
    }
  }
  
  if (i == 25){
    # Calculate the difference measure between the current output and the previous one
    # For example, you can use the sum of absolute differences. Depending on your needs, you might want to use a different measure.
    #sign_check <- all(outputs[[i + 1]] > outputs[[i]] | outputs[[i + 1]] > outputs[[1]])
    sign_check <- TRUE
  } 
  
  # Clear the region to reset and Increase the iteration number
  reset_region <- NULL
  iter_region <- NULL
  reset_area_producer[i+1] <- list(NULL)
  reset_area_wo_producer[i+1] <- list(NULL)
  reset_area[i+1] <- list(NULL)
  
  sl4 <-"NATDEF.sl4"
  
  source_tracker <- file.path(parent_folder, "2_Model", sl4)
  destination_tracker <- file.path(save_path, paste0(sub("\\.([^.]+)$", paste0("_", i, ".\\1"), sl4)))
  
  result_tracker <- file.copy(source_tracker, destination_tracker, overwrite = TRUE)
  
  if (result_tracker) {
    print(paste("File copy successful for", bu_file))
  } else {
    print(paste("File copy failed for", bu_file))
  }
  
  i <- i + 1
}

## Last, restore the BU from the original RunGTAP
# List of BU files to copy
bu_files <- c("NATDEF.har", "NATDEF.sl4", "NATDEF.cmf")

# Source and destination folders are as per your setup
source_folder_copy <- file.path(parent_folder, "2_Model", "BU/")
destination_folder_paste <- GTAPAEZ_path

# Loop to iterate through each BU file
for (bu_file in bu_files) {
  
  # Full path of the source and destination files
  source_file_path_copy <- file.path(source_folder_copy, bu_file)
  destination_file_path_paste <- file.path(destination_folder_paste, bu_file)
  
  # Check if the source file exists
  if (!file.exists(source_file_path_copy)) {
    print(paste("Source file does not exist:", bu_file))
    next
  }
  
  # Check if the destination folder exists
  if (!dir.exists(destination_folder_paste)) {
    print("Destination folder does not exist.")
    next
  }
  
  # Attempt to copy and overwrite if the file already exists
  result <- file.copy(source_file_path_copy, destination_file_path_paste, overwrite = TRUE)

  
  # Check the result
  if (result) {
    print(paste("File copy successful for", bu_file))
  } else {
    print(paste("File copy failed for", bu_file))
  }
  # Check the result
  
}

print(paste( scenario,"Processed"))
}
}
}



tableau_db <- data.frame()

for (approach in list_approach){
  for (p in list_parameter){  
    for (name in length(scenarios)) {
      
      #approach = "Diplomatic"
      #p = "qes"
      #name = 1
      
      iter_db <- data.frame()
      reset_db <- data.frame() 
      ev_db <- data.frame()# Create an empty data frame to store the aggregated data
      luc_db <- data.frame()
      
      scenario_path <- file.path(parent_folder, "3_Output",approach, paste0(p, "_", run_tag), scenarios[[name]])   # V14
      
      file_iter_names <- list.files(path = scenario_path, pattern = "Iter_Region_\\d+\\.txt", full.names = TRUE)
      file_reset_names <- list.files(path = scenario_path, pattern = "Reset_Region_\\d+\\.txt", full.names = TRUE)
      file_ev_names <- list.files(path = scenario_path, pattern = "Equivalent_Variation_round_\\d+\\.txt", full.names = TRUE)
      file_luc_names <- list.files(path = scenario_path, pattern = "Forest_LU_Region_Ha_\\d+\\.txt", full.names = TRUE)
      
      for(file in file_iter_names) {
        # Read the txt file into a data frame
        iter_raw <- read.table(file, header = FALSE, sep = "\t", col.names= "Country")  # Assuming the files are tab-separated
        if(nrow(iter_raw) == 0) {
          warning(paste("File is empty:", file))
          next
        }
        # Extract the iteration number from the filename
        iteration_number <- gsub(".*Iter_Region_([0-9]+)\\.txt$", "\\1", file)
        # Add new columns to iter_raw with the iteration number and scenario
        iter_raw$Iteration <- as.integer(iteration_number)
        iter_raw$Scenario <- scenarios[[name]]
        iter_raw$Club <- "inside"
        # Append the data to the aggregated data frame
        iter_db <- bind_rows(iter_db, iter_raw)
      }
      
      for(file in file_reset_names) {
        # Read the txt file into a data frame
        reset_raw <- read.table(file, header = FALSE, sep = "\t", col.names= "Country")  # Assuming the files are tab-separated
        if(nrow(reset_raw) == 0) {
          warning(paste("File is empty:", file))
          next
        }
        # Extract the iteration number from the filename
        reset_number <- gsub(".*Reset_Region_([0-9]+)\\.txt$", "\\1", file)
        # Add new columns to iter_raw with the iteration number and scenario
        reset_raw$Iteration <- as.integer(reset_number)
        reset_raw$Scenario <- scenarios[[name]]
        reset_raw$Club <- "outside"
        # Append the data to the aggregated data frame
        reset_db <- bind_rows(reset_db, reset_raw)
      }
      
      for(file in file_luc_names) {
        # Read the txt file into a data frame
        
        #file = "C:/runGTAP375/Game_theory_2024/3_Output/Diplomatic/qes/Scenario_D/Forest_LU_Region_Ha_0.txt"
        
        luc_raw <- read.table(file, header = FALSE, sep = " ",)  # Assuming the files are tab-separated
        
        # Add new columns to iter_raw with the iteration number and scenario
        luc_number <- gsub(".*Forest_LU_Region_Ha_([0-9]+)\\.txt$", "\\1", file)
        
        luc_raw$Iteration <- as.integer(luc_number)
        luc_raw$Scenario <- scenarios[[name]]
        
        luc_raw <- luc_raw %>% rename (Country = V1, 
                                       aez1 = V2,aez2 = V3,aez3 = V4,aez4 = V5,aez5 = V6,aez6 = V7,
                                       aez7 = V8,aez8 = V9,aez9 = V10,aez10 = V11,aez11 = V12,aez12 = V13,
                                       aez13 = V14,aez14 = V15,aez15 = V16,aez16 = V17,aez17 = V18,aez18 = V19)
        
        # Append the data to the aggregated data frame
        luc_db <- bind_rows(luc_db, luc_raw)
      }
      
      for(file in file_ev_names) {
        # Read the txt file into a data frame
        
        #file  = "C:/runGTAP375/Game_theory_2024/3_Output/Diplomatic/qes/Scenario_D/Equivalent_Variation_round_0.txt" 
        
        ev_raw <- read.table(file, header = FALSE, sep = " ", col.names= c("Country", "EV_previous_round", "EV","Iteration"))  # Assuming the files are tab-separated
        # Add new columns to iter_raw with the iteration number and scenario
        ev_raw$Scenario <- scenarios[[name]]
        # Append the data to the aggregated data frame
        ev_db <- bind_rows(ev_db, ev_raw)
      }
    
      db_df <- rbind(iter_db, reset_db)
      ev_db['Iteration'] <- (ev_db['Iteration']-1)
    
      ev_db <- inner_join( luc_db, ev_db, by=c('Country'='Country', 'Iteration'='Iteration', 'Scenario'='Scenario'))
    
      db <- inner_join(db_df, ev_db, by=c('Country'='Country', 'Iteration'='Iteration', 'Scenario'='Scenario'))
    
      df_producer <- data.frame(Country = list_producer_countries, tag = "producer")
      df_non_producer <- data.frame(Country = list_non_producer_countries, tag = "non-producer")
    
      # Combine the two data frames
      df_combined <- rbind(df_producer, df_non_producer)
      #tag tehm
      db_tagged <- merge(db, df_combined, by = "Country", all.x = TRUE)
      db_tagged['parameter'] <- p
      db_tagged['Approach'] <- approach
      
      condition <- db_tagged$Iteration == 0
      condition_2 <- db_tagged$Country == 'eu27'
      # # Use a temporary variable to swap values
      temp <- db_tagged$EV[condition]
      db_tagged$EV[condition] <- db_tagged$EV_previous_round[condition]
      db_tagged$EV_previous_round[condition] <- temp
      db_tagged$Club[condition_2] <- 'inside'
      
      
      #save them
      #save_path <- file.path(parent_folder, "4_DB",approach,p,"Database_GTAPAEZ_results_2024.xlsx")
      #write_xlsx(db_tagged, save_path)
      
      tableau_db <- bind_rows(tableau_db,db_tagged)
      
      iter_db <- NULL
      reset_db <- NULL
      ev_db <- NULL
      file_iter_names <- NULL
      file_reset_names <- NULL
      file_ev_names <- NULL
      db_tagged <- NULL
    }
  }
}

tableau_db_agg <- tableau_db

# 
 tableau_db_agg $Boreal <- rowSums(tableau_db_agg [, 5:10])
 tableau_db_agg $Temperate <- rowSums(tableau_db_agg [, 11:16])
 tableau_db_agg $Tropical <- rowSums(tableau_db_agg [, 17:22])
# 
 tableau_db_agg <- tableau_db_agg[,-c( 5:10)]
 tableau_db_agg <- tableau_db_agg[,-c( 5:10)]
 tableau_db_agg <- tableau_db_agg[,-c( 5:10)]
# 
# 
# #save the tableau db
 save_path <- file.path(parent_folder, "4_DB",paste0("Database_GTAPAEZ_all_results_2024_agg_", run_tag, ".csv"))   # V14
 write.csv(tableau_db_agg , save_path, row.names = FALSE)

mapping <- list(
  angola = c('AGO'),
  drc = c('COD'),
  argentina = c('ARG'),
  bolivia = c('BOL'),
  brasil = c('BRA'),
  canada = c('CAN'),
  china = c('CHN'),
  colombia = c('COL'),
  eastasia = c('HKG', 'MAC', 'PRK', 'TWN', 'MNG', 'BRN'),
  EFTA = c('ISL', 'NOR', 'CHE'),
  eu27 = c('AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 
           'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 
           'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE', 'REU', 'GLP', 'MTQ'),
  
  ghana = c('GHA'),
  india = c('IND'),
  indonesia = c('IDN'),
  ivorycoast = c('CIV'),
  japan = c('JPN'),
  korea = c('KOR'),
  latinamer = c('AIA', 'ATG', 'ABW', 'BHS', 'BRB', 'VGB', 'CYM', 'CUB', 'DMA', 
                'DOM', 'GRD', 'HTI', 'JAM', 'MSR', 'PRI', 'KNA', 'LCA', 'VCT', 
                'TTO', 'TCA', 'VIR', 'BLZ', 'CRI', 'SLV', 'GTM', 'HND', 'NIC', 'PAN', 
                'CHL', 'ECU', 'FLK', 'GUF', 'GUY', 'SGS', 'SUR', 'URY'),  
  
  madagascar = c('MDG'),
  malasya = c('MYS'),
  mena = c( 'IRN', 'IRQ', 'ISR', 'JOR',
           'KWT', 'LBN', 'OMN', 'QAT', 'SAU', 'SYR', 'TUR', 'ARE', 'YEM'),
  mexico = c('MEX'),
  mozambique = c('MOZ'),
  myanmar = c('MMR'),
  newzealand = c('NZL'),
  nigeria = c('NGR'),
  oceania = c('AUS', 'FJI', 'NCL', 'PNG', 'SLB', 'VUT', 'GUM', 'KIR', 'MHL', 
              'FSM', 'NRU', 'MNP', 'PLW', 'UMI', 'ASM', 'COK', 'PYF', 'NIU', 'PCN',
              'WSM', 'TKL', 'TON', 'TUV', 'WLF'),
  paraguay = c('PRY'),
  peru = c('PER'),
  restofworld = c('IOT', 'ATF', 'BVT', 'BMU', 'GRL', 'SPM', 'ATA', 'KAZ', 
                  'KGZ', 'TJK', 'TKM', 'UZB', 'ARM', 'AZE', 'GEO', 'BLR', 
                  'MDA', 'UKR', 'GGY', 'JEY', 'FRO', 'IMN', 'ALB', 'AND',
                  'BIH', 'GIB', 'VAT', 'MNE', 'MKD', 'SMR', 'SRB', 'LIE', 'MCO'),
  russia = c('RUS'),
  seasia = c('KHM', 'LAO', 'PHL', 'SGP', 'THA', 'TLS', 'VNM'),
  southasia = c('AFG', 'BGD', 'BTN',  'MDV', 'NPL', 'PAK', 'LKA'),
  nafr = c('DZA', 'EGY','MAR','TUN','LBY','ESH','MRT'),
  wafr = c('BEN', 'BFA','GIN','SEN','TGO','CPV','GMB',  
           'GNB', 'LBR', 'MLI','NER','SHN','SLE'),
  cafr = c('CMR','CAF','TCD', 'COG', 
           'GNQ','GAB','STP','BDI'),
  eafr = c('ETH','KEN','MUS','RWA','UGA','TZA','COM','DJI',
           'ERI','MYT','SYC','SOM','SDN','SSD'),
  safr = c('MWI', 'ZMB', 'ZWE', 'BWA','NAM','ZAF','SWZ', 'LSO'),
  uk = c('GBR'),
  efta = c('NOR','ISL','CHE','LIE'),
  uruguay = c('URY'),
  us = c('USA'),  
  venezuela = c('VEN')
)

#Function to split country groups into separate rows
 split_countries <- function(row) {
   countries <- mapping[[row$Country]]
   data.frame(
     ISO = countries,
     country_group = rep(row$Country, length(countries)),
     Boreal_High1Humidity = rep(row$aez18, length(countries)),
     Boreal_Normal1Humidity = rep(row$aez17, length(countries)),
     Boreal_Low1Humidity = rep(row$aez16, length(countries)),
     Boreal_Moist1Semiarid = rep(row$aez15, length(countries)),
     Boreal_Dry1Semiarid = rep(row$aez14, length(countries)),
     Boreal_Arid1Arid= rep(row$aez13, length(countries)),

     Temperate_High1Humidity = rep(row$aez12, length(countries)),
     Temperate_Normal1Humidity = rep(row$aez11, length(countries)),
     Temperate_Low1Humidity = rep(row$aez10, length(countries)),
     Temperate_Moist1Semiarid = rep(row$aez9, length(countries)),
     Temperate_Dry1Semiarid = rep(row$aez8, length(countries)),
     Temperate_Arid1Arid= rep(row$aez7, length(countries)),

     Tropical_High1Humidity = rep(row$aez6, length(countries)),
     Tropical_Normal1Humidity = rep(row$aez5, length(countries)),
     Tropical_Low1Humidity = rep(row$aez4, length(countries)),
     Tropical_Moist1Semiarid = rep(row$aez3, length(countries)),
     Tropical_Dry1Semiarid = rep(row$aez2, length(countries)),
     Tropical_Arid1Arid= rep(row$aez1, length(countries)),

     Approach = rep(row$Approach, length(countries)),
     Iteration = rep(row$Iteration, length(countries)),
     Scenario = rep(row$Scenario, length(countries)),
     Club = rep(row$Club, length(countries)),
     EV_previous_round = rep(row$EV_previous_round, length(countries)),
     EV = rep(row$EV, length(countries)),
     tag = rep(row$tag, length(countries)),
     parameter = rep(row$parameter, length(countries))
   )
 }

 # Apply the function to each row and concatenate the results
 split_df <- do.call(rbind, lapply(1:nrow(tableau_db), function(i) split_countries(tableau_db[i, ])))

 split_df <- split_df %>%
   rename(Country = country_group)

 split_df  <- split_df %>%
   pivot_longer(
     cols = starts_with("Boreal_") | starts_with("Temperate_") | starts_with("Tropical_"),
     names_to = c("Climate_Type", "Humidity_Level"),
     names_sep = "_",
     values_to = "Value"
   )

save_path <- file.path(parent_folder, "4_DB",paste0("Database_GTAPAEZ_all_results_2024_", run_tag, ".csv"))   # V14
write.csv(split_df , save_path, row.names = FALSE)
