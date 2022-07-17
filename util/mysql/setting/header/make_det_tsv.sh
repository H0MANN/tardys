#!/bin/sh

. ~/taoics/tardys/aliases.sh


if [ ! -f tardys_header_det.xlsx ]; then
    pretty_echo "'tardys_header_det.xlsx' not found!! Bye." "r"
    exit 1;
fi


rm -f /tmp/det_master.tsv_from_xls det_master.tsv &&


## Excel --> tsv.
pretty_echo "Converting Excel into tsv..." "g" &&
python3 xlsx2csv.py tardys_header_det.xlsx -d tab -s 1 > /tmp/det_master.tsv_from_xls &&
pretty_echo "Done." "g" &&


## det
pretty_echo "Creating 'det_master.tsv'." "g" &&
awk -F "\t" '{print $2"\t"$3"\t"$4"\t"$5"\t"$6"\t"$7"\t"$8"\t"$9"\t"$10"\t"$11"\t"$12"\t"$13"\t"$14"\t"$15"\t"$16"\t"$17}' /tmp/det_master.tsv_from_xls > det_master.tsv &&
pretty_echo "Done." "g" &&


rm -f /tmp/det_master.tsv_from_xls


echo ""
pretty_echo "Execute the following commands to update the corresponding SQL tables." "c"
pretty_echo "python2.7 create_header_table.py det_b1_master.tsv" "c"
pretty_echo "python2.7 create_header_table.py det_b2_master.tsv" "c"
pretty_echo "python2.7 create_header_table.py det_r1_master.tsv" "c"
pretty_echo "python2.7 create_header_table.py det_r2_master.tsv" "c"
