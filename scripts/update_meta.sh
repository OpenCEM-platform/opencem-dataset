#!/usr/bin/env bash

gawk -F, 'NR > 1 {count++} END {print count}' data/measurements/*.csv > /tmp/measurement_rows.$$ &
gawk -F, 'NR > 1 {count++} END {print count}' data/context/*.csv > /tmp/context_records.$$ &
gawk -F',' 'NR > 1 {if ($1 < min || min == "") min=$1} END {print strftime("%Y-%m-%d %H:%M:%S", min)}' data/measurements/*.csv > /tmp/measurement_start.$$ &
gawk -F',' 'NR > 1 {timestamp = $1 + 0; if (timestamp > max || max == "") max = timestamp} END {print strftime("%Y-%m-%d %H:%M:%S", max)}' data/measurements/*.csv > /tmp/measurement_end.$$ &
gawk -F',' 'NR > 1 {if ($2 < min || min == "") min=$2} END {print strftime("%Y-%m-%d %H:%M:%S", min)}' data/context/*.csv > /tmp/context_start.$$ &
gawk -F',' 'NR > 1 {timestamp = $2 + 0; if (timestamp > max || max == "") max = timestamp} END {print strftime("%Y-%m-%d %H:%M:%S", max)}' data/context/*.csv > /tmp/context_end.$$ &
gawk -F',' 'NR > 1 {days[strftime("%D", $1)]++} END {print length(days)}' data/measurements/*.csv > /tmp/measurement_days.$$ &
gawk -F',' 'NR > 1 {days[strftime("%D", $2)]++} END {print length(days)}' data/context/*.csv > /tmp/context_days.$$ &
gawk -F, 'NR > 1 {if ($2 != prev_node) {prev_node=$2; prev_ts[$2]=0} else {freqs[$2][$1-prev_ts[$2]]++} prev_ts[$2]=$1} END {n=0; for (node in freqs) {for (f in freqs[node]) {for (i=0; i<freqs[node][f]; i++) {vals[n++]=f}}}; asort(vals); if (n%2) {print vals[n/2]} else {print (vals[n/2-1]+vals[n/2])/2}}' data/measurements/*.csv > /tmp/median.$$ &
gawk -F',' '{if ($2 != "inverter") inverters[$2]=1} END {print length(inverters)}' data/measurements/*.csv > /tmp/inverters.$$ &
cat data/measurements/* | head -n1 | awk -F',' '{print NF}' > /tmp/measurement_columns.$$ &
wait
DATA_SIZE=$(du -sh data | awk '{print $1}')

MEASUREMENT_ROWS=$(</tmp/measurement_rows.$$)
CONTEXT_RECORDS=$(</tmp/context_records.$$)
MEASUREMENT_START=$(</tmp/measurement_start.$$)
MEASUREMENT_END=$(</tmp/measurement_end.$$)
MEASUREMENT_DAYS=$(</tmp/measurement_days.$$)
CONTEXT_START=$(</tmp/context_start.$$)
CONTEXT_END=$(</tmp/context_end.$$)
CONTEXT_DAYS=$(</tmp/context_days.$$)
MEASUREMENT_COLUMNS=$(</tmp/measurement_columns.$$)
INVERTERS=$(</tmp/inverters.$$)
MEDIAN=$(</tmp/median.$$)

echo "| Measurement rows | $MEASUREMENT_ROWS |"
echo "| Context records | $CONTEXT_RECORDS |"
echo "| Measurement coverage | $MEASUREMENT_START UTC to $MEASUREMENT_END UTC |"
echo "| Context coverage | $CONTEXT_START UTC to $CONTEXT_END UTC |"
echo "| Measurement days | $MEASUREMENT_DAYS unique UTC dates |"
echo "| Context days | $CONTEXT_DAYS UTC dates "|
echo "| Measurement interval | Median $MEDIAN seconds per inverter |"
echo "| Inverters | $INVERTERS |"
echo "| Measurement columns | $MEASUREMENT_COLUMNS |"
echo "| Repository data size | About "$DATA_SIZE"B |"

rm /tmp/*.$$
