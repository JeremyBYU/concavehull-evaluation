library(gglogo)

# check that all letters and digits are nicely shaped:
new_alphabet <- createPolygons(c("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"), font="Garamond")

print(new_alphabet)
write.csv(new_alphabet, "/home/jeremy/Documents/UMICH/concavehull-evaluation/test_fixtures/alphabet/alphabet.csv")