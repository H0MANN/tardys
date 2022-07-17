#!/bin/bash -l


##########################################################################
export PATH

alias less="less -R"
alias mv="mv -i"
alias cp="cp -i"
alias rm="rm -i"
alias ls='ls --color=auto'
alias ll='ls -alF'
alias la='ls -A'
alias grep='grep --color=auto'
alias disp='display'
alias free='free -t'

export XPA_METHOD=local

#export LESS='-R'
#export LESSOPEN='| /usr/bin/src-hilite-lesspipe.sh %s'

#alias xgterm='xgterm -sb'
#alias tree='tree -aF --dirsfirst'


##########################################################################
export INSTNAME=swims

export TAOICSHOME=${HOME}/taoics
export TAODOCSHOME=${HOME}/taodocs
export TAOGINGAHOME=${HOME}/taoginga

export COMMONHOME=${TAOICSHOME}/common

export INSTHOME=${TAOICSHOME}/${INSTNAME}

export DEVICEHOME=${INSTHOME}/device

export PYTHONPATH=${HOME}:${PYTHONPATH}
export PYTHONPATH=${TAODOCSHOME}/tardys_docs/g2cam:${PYTHONPATH}
export PYTHONPATH=${TAOGINGAHOME}/common-ginga:${PYTHONPATH}
export PYTHONPATH=${TAOGINGAHOME}/tardys-ginga:${PYTHONPATH}

#export PYTHON27=`which python2.7`  ## cron fails...
export PYTHON27=/usr/local/bin/python2.7

alias get_config="${PYTHON27} ${COMMONHOME}/util/get_config.py"
alias icsboot="${PYTHON27} ${COMMONHOME}/util/icsboot.py"
#alias fitsview="sh ${INSTHOME}/fitsview.sh"
alias fitsview="${PYTHON27} ${INSTHOME}/fitsview.py"
alias webcam="sh ${INSTHOME}/webcam.sh"
alias start_webcam="sh ${INSTHOME}/webcam.sh --start"
alias stop_webcam="sh ${INSTHOME}/webcam.sh --stop"
#alias hxrg="sh ${DEVICEHOME}/det/proc_vmware.sh"
alias update_status_table="${PYTHON27} ${INSTHOME}/util/mysql/setting/status/update_status_table.py"
#alias ping_check=`get_config ping_check dest | sed -e 's/,/\n/g' | awk '{print "ping -c 1 "$1" >> /dev/null 2>&1; echo "$1":  $?"}'`
alias check_ping="${PYTHON27} ${INSTHOME}/check_ping.py"


##########################################################################
pretty_echo ()
{
    msg=$1;
    color=$2;

    case ${color} in
        "k") val=30 ;;
        "r") val=31 ;;
        "g") val=32 ;;
        "y") val=33 ;;
        "b") val=34 ;;
        "m") val=35 ;;
        "c") val=36 ;;
        "w") val=37 ;;
    esac

    echo -e "\e[${val}m${msg}\e[m" 1>&2;
}


##########################################################################
load_passwd ()
{
    pretty_echo "Loading the password ..." "g"
    export PASSWD=`get_config sudo passwd | xargs cat`
    if [ "${PASSWD}" = "" ]; then
        pretty_echo "Failed to load the password." "r"
        exit 1
    else
        echo ${PASSWD} | sudo -S ls >> /dev/null #2>&1
        echo ""
        pretty_echo "... Succeeded.\n" "g"
    fi

}


##########################################################################
logtail ()
{
    tail -F -n 20 $@ | ${PYTHON27} ${COMMONHOME}/util/colored_log.py
}


##########################################################################
alias shutdown_detPCs="sh ${INSTHOME}/shutdown_detPCs.sh"
alias shutdown_OBCP="sh ${INSTHOME}/shutdown_OBCP.sh"


#alias cooler_mosu_on="python2.7 ${DEVICEHOME}/cooler/exec.py mosu on"
#alias cooler_mosu_off="python2.7 ${DEVICEHOME}/cooler/exec.py mosu off"
#alias cooler_main_on="python2.7 ${DEVICEHOME}/cooler/exec.py main on"
#alias cooler_main_off="python2.7 ${DEVICEHOME}/cooler/exec.py main off"

alias coldhead_main_on="python2.7 ${DEVICEHOME}/pdu/exec.py on COLDHEAD_MAIN"
alias coldhead_main_off="python2.7 ${DEVICEHOME}/pdu/exec.py off COLDHEAD_MAIN"
alias coldhead_mosu_on="python2.7 ${DEVICEHOME}/pdu/exec.py on COLDHEAD_MOSU"
alias coldhead_mosu_off="python2.7 ${DEVICEHOME}/pdu/exec.py off COLDHEAD_MOSU"

alias precool_ramp="crontab < ${INSTHOME}/cron_totoro_precool_ramp"
alias precool_keep77="crontab < ${INSTHOME}/cron_totoro_precool_keep77; python2.7 ${DEVICEHOME}/tpr_331/exec.py setp 1 77;python2.7 ${DEVICEHOME}/tpr_332/exec.py setp 1 77"

#alias tpr331_htr_high="python2.7 ${DEVICEHOME}/tpr_331/exec.py hrange 3"
#alias tpr331_htr_mid="python2.7 ${DEVICEHOME}/tpr_331/exec.py hrange 2"
#alias tpr331_htr_low="python2.7 ${DEVICEHOME}/tpr_331/exec.py hrange 1"
#alias tpr331_htr_off="python2.7 ${DEVICEHOME}/tpr_331/exec.py hrange 0"
#alias tpr332_htr_high="python2.7 ${DEVICEHOME}/tpr_332/exec.py hrange 3"
#alias tpr332_htr_mid="python2.7 ${DEVICEHOME}/tpr_332/exec.py hrange 2"
#alias tpr332_htr_low="python2.7 ${DEVICEHOME}/tpr_332/exec.py hrange 1"
#alias tpr332_htr_off="python2.7 ${DEVICEHOME}/tpr_332/exec.py hrange 0"

alias resume_setp_after_ciax="python2.7 ${DEVICEHOME}/resume_setp_after_ciax.py"

alias mosu_car_heater_on="python2.7 ${DEVICEHOME}/pdu/exec.py on MOSU_CAR_HEATER"
alias mosu_car_heater_off="python2.7 ${DEVICEHOME}/pdu/exec.py off MOSU_CAR_HEATER"
alias mosu_arm_heater_on="python2.7 ${DEVICEHOME}/pdu/exec.py on MOSU_ARM_HEATER"
alias mosu_arm_heater_off="python2.7 ${DEVICEHOME}/pdu/exec.py off MOSU_ARM_HEATER"


#setpoint_follow_camera ()
#{
#    crontab <<EOF
#    $(cat cron_totoro_master cron_totoro_cooling_APS)
#    EOF
#}


#setpoint_keep_77K ()
#{
#    crontab <<EOF
#    $(cat cron_totoro_master cron_totoro_c
#    EOF
#}

