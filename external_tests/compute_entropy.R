library(pracma)

wd = "~/Desktop/CINTESIS/Rotinas/hrfanalyse-master"
setwd(wd)

ds_path = "~/Desktop/Traces_clean/"

ds_list = list.files("~/Desktop/Traces_clean", full.names = TRUE)

# example
# f1 =ts(read.csv("~/Desktop/Traces_clean/caso_100,MMNR.TxSP3", header = FALSE))
# apen_t_0.1 = approx_entropy(f1 ,edim = 2, r = 0.1 * sd(f1))

#### apen ####
## read all csv files and compute aprox entropy 
tol = 0.1
apen_0.1_list = c()
for(name in ds_list){
  print(name)
  wave = ts(read.csv(name, header = FALSE))
  apen_0.1_list[length(apen_0.1_list)+1] = approx_entropy(ts = wave, edim = 2, r = tol * sd(wave))
}
gc() # better clean the memory cus entropy uses to much

## read all csv files and compute aprox entropy 
tol = 0.15
apen_0.15_list = c()
for(name in ds_list){
  print(name)
  wave = ts(read.csv(name, header = FALSE))
  apen_0.15_list[length(apen_0.15_list)+1] = approx_entropy(ts = wave, edim = 2, r = tol * sd(wave))
}
gc() # better clean the memory cus entropy uses to much

## read all csv files and compute aprox entropy 
tol = 0.2
apen_0.2_list = c()
for(name in ds_list){
  print(name)
  wave = ts(read.csv(name, header = FALSE))
  apen_0.2_list[length(apen_0.2_list)+1] = approx_entropy(ts = wave, edim = 2, r = tol * sd(wave))
}
gc() # better clean the memory cus entropy uses to much

apen_entropy_df = data.frame(apen_0.1_list, apen_0.15_list, apen_0.2_list, row.names = ds_list)

#### sampen ####

## read all csv files and compute aprox entropy 
tol = 0.1
sampen_0.1_list = c()
for(name in ds_list){
  print(name)
  wave = ts(read.csv(name, header = FALSE))
  sampen_0.1_list[length(sampen_0.1_list)+1] = sample_entropy(ts = wave, edim = 2, r = tol * sd(wave))
}
gc() # better clean the memory cus entropy uses to much

## read all csv files and compute aprox entropy 
tol = 0.15
sampen_0.15_list = c()
for(name in ds_list){
  print(name)
  wave = ts(read.csv(name, header = FALSE))
  sampen_0.15_list[length(sampen_0.15_list)+1] = sample_entropy(ts = wave, edim = 2, r = tol * sd(wave))
}
gc() # better clean the memory cus entropy uses to much

## read all csv files and compute aprox entropy 
tol = 0.2
sampen_0.2_list = c()
for(name in ds_list){
  print(name)
  wave = ts(read.csv(name, header = FALSE))
  sampen_0.2_list[length(sampen_0.2_list)+1] = sample_entropy(ts = wave, edim = 2, r = tol * sd(wave))
}
gc() # better clean the memory cus entropy uses to much

sampen_entropy_df = data.frame(sampen_0.1_list, sampen_0.15_list, sampen_0.2_list, row.names = ds_list)