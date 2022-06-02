import React, { useState, useEffect, useContext } from 'react';
import AllCalenders from './AllCalenders';
import { ButtonNew, Loading } from '@usernames/sentieoui';
import { MainCompContext } from '../../contexts/MainCompContext';
import { getWatchlists } from '../../API/GetWatchlists';
import { getUserAccounts } from '../../API/GetUserAccounts';
import { addICSDataGoogle , addICSDataOutlook } from '../../API/calendarexport';
import { fetchEarningsEvents } from '../../API/FetchEarningsEvents';
import { getEarningsEventArray } from '../../utils/calendarEvents';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown, faChevronRight } from '@fortawesome/free-solid-svg-icons';
import CalendarWizard from '../../CalendarWizard';
import { getAllCalendars } from '../../API/GetAllCalendars';

//import WatchlistWizard from '../../WatchlistWizard';


function MenuMain(props) {
    const {
        calendarsCx,
        activeWatchlistsCx,
        exportactiveWatchlistsCx,
        startTSCx,
        endTSCx,
        allEventsCx,
        calendarEventsCx,
        calendarLoadingCx,
        EarningsEventsCx,
        CalendarSelectedFilterCx,
        isWatchlistLoadingCx,
        isexportWatchlistDataLoadingCx,
        rightEarningsEventCx,
        rightEarningsEventDaysCx,
        isWatchlistDataLoadingCx,
    } = useContext(MainCompContext);
    
    const [calendars, setCalendars] = calendarsCx;
    const [showType, setShowType] = useState(false);
    const [googleFlag, setGoogleFlag] = useState("none");
    const [outlookFlag, setOutlookFlag] = useState("none");
    const [displayType, setDisplayType] = useState(false);
    const [watchlists, setWatchlists] = useState([]);
    const [activeWatchlists, setActiveWatchlists] = activeWatchlistsCx;
    const [exportactiveWatchlists, setexportActiveWatchlists] = exportactiveWatchlistsCx;
    const [allEvents, setAllEvents] = allEventsCx;
    const [calendarEvents, setCalendarEvents] = calendarEventsCx;
    const [isWatchlistLoading, setIsWatchlistLoading] = isWatchlistDataLoadingCx;
    const [isexportWatchlistLoading, setIsexportWatchlistLoading] = isexportWatchlistDataLoadingCx;
    const [isWatchlistAPILoading, setIsWatchlistAPILoading] = isWatchlistLoadingCx;
    const [calendarLoading, setCalendarLoading] = calendarLoadingCx;
    const [EarningsEvents, setEarningsEvents] = EarningsEventsCx;
    const [sentieoWatchlist, setSentieoWatchlist] = useState(true);
    const [calendarBulkAction, setCalendarBulkAction] = useState(true);
    const [CalendarSelectedFilter, setCalendarSelectedFilter] = CalendarSelectedFilterCx;
    const [calendarSelectedFilterlocal, setCalendarSelectedFilterlocal] = useState([]);
    const [isWatchlistOpen, setIsWatchlistOpen] = useState(true);
    const [WatchlistOpen, setWatchlistOpen] = useState(true);
    const [isGmailCalendarOpen, setIsGmailCalendarOpen] = useState(true);
    const [isOutlookCalendarOpen, setIsOutlookCalendarOpen] = useState(true);
    const [isSeeMoreOpen, setIsSeeMoreOpen] = useState(false);
    const [userData, setUserData] = useState('');
    const [rightEarningsEvent, setRightEarningsEvent] = rightEarningsEventCx;
    const [rightEarningsEventDays, setRightEarningsEventDays] = rightEarningsEventDaysCx;

    const getFormattedDate = (lastSyncTimestamp) => {
        let formattedDateTimeStr;
        let config = {
            day: '2-digit',
            year: '2-digit',
            month: 'short',
            hour: 'numeric',
            minute: 'numeric',
            hour12: true,
        };
        formattedDateTimeStr = lastSyncTimestamp
            .toLocaleDateString('en-IN', config)
            .replaceAll('-', ' ')
            .toUpperCase();

        return formattedDateTimeStr;
    };

    const callGetUsersAccountsApi = async () => {
        const userData = await getUserAccounts();
        return userData;
    };

    const getLastSyncTime = (email) => {
        let lastSyncTime;
        userData &&
            userData.forEach((item) => {
                if (item['emailAddress'] === email) {
                    lastSyncTime = item['lastSynced'];
                }
            });
        return getFormattedDate(new Date(lastSyncTime * 1000));
    };

    useEffect(() => {
        callGetUsersAccountsApi().then((res) => {
            setUserData(res);
        });
        let watchlistBulkCheck = JSON.parse(window.localStorage.getItem('watchlistBulkCheck'));
        if (watchlistBulkCheck !== null) {
            setSentieoWatchlist(watchlistBulkCheck);
        } else {
            window.localStorage.setItem('watchlistBulkCheck', JSON.stringify(sentieoWatchlist));
        }

        let calendarsBulkCheck = JSON.parse(window.localStorage.getItem('calendarsBulkCheck'));
        if (calendarsBulkCheck !== null) {
            setCalendarBulkAction(calendarsBulkCheck);
        } else {
            window.localStorage.setItem('calendarsBulkCheck', JSON.stringify(calendarBulkAction));
        }
        const interval = setInterval(() => {
            callGetUsersAccountsApi().then((res) => {
                setUserData(res);
            });
        }, 1000 * 60 * 15);
        return () => clearInterval(interval);
    }, []);

    const isAvailable = (arg) => {
        for (let i in calendars) {
            if (calendars[i].provider == arg) {
                return true;
            }
        }
        return false;
    };

    const onClickBulkWatchlistCheckbox = (value) => {
        if (value) {
            setActiveWatchlists(watchlists);
            window.localStorage.setItem('activeWatchlists', JSON.stringify(watchlists));
            window.localStorage.setItem('watchlistBulkCheck', true);
        } else {
            setActiveWatchlists([]);
            window.localStorage.setItem('activeWatchlists', JSON.stringify([]));
            window.localStorage.setItem('watchlistBulkCheck', false);
        }
        setSentieoWatchlist(value);
    };

    const onClickBulkCalendarCheckbox = (value) => {
        setCalendarLoading(true);
        if (value) {
            let calendarsMapped = calendars.map((calendar) => calendar.calendarId);
            setCalendarSelectedFilter(calendarsMapped);
            window.localStorage.setItem('activeCalendars', JSON.stringify(calendarsMapped));
            window.localStorage.setItem('calendarsBulkCheck', true);
        } else {
            setCalendarSelectedFilter([]);
            window.localStorage.setItem('activeCalendars', JSON.stringify([]));
            window.localStorage.setItem('calendarsBulkCheck', false);
        }
        setCalendarBulkAction(value);
        setCalendarLoading(false);
    };

    const onClickClearAllButton = () => {
        setActiveWatchlists([]);
        setSentieoWatchlist(false);
        window.localStorage.setItem('activeWatchlists', JSON.stringify([]));
        window.localStorage.setItem('watchlistBulkCheck', false);
    };

    const onClickCalendarClearAllButton = () => {
        setCalendarLoading(true);
        setCalendarSelectedFilter([]);
        setCalendarBulkAction(false);
        window.localStorage.setItem('activeCalendars', JSON.stringify([]));
        window.localStorage.setItem('calendarsBulkCheck', false);
        setCalendarLoading(false);
    };

    useEffect(async () => {
        let resultWatchlists = await getWatchlists();
        
        resultWatchlists.sort((a, b) => {
            if (a < b) {
                return -1;
            }
            if (a > b) {
                return 1;
            }
            return 0;
        });

        setWatchlists(resultWatchlists);
        let watchlistsSelected = JSON.parse(window.localStorage.getItem('activeWatchlists'));
        if (watchlistsSelected !== null) {
            setActiveWatchlists(watchlistsSelected);
        } else {
            setActiveWatchlists(resultWatchlists);
        }
        setCalendarSelectedFilterlocal(CalendarSelectedFilter);
        setIsWatchlistAPILoading(false);
    }, []);

    const fetchWatchlistData = async (data) => {
        
        const calendarEarningsEvents = [];
      
        setEarningsEvents(calendarEarningsEvents);
        setAllEvents((prev) => {
            let calEvents = [];
            if (prev.length > 0) {
                calEvents = prev.filter((event) => !event.isEarningsEvent);
            }
            let events = [...calEvents, ...getEarningsEventArray(calendarEarningsEvents)];
            return events;
        });
        setIsWatchlistLoading(false);
        setIsexportWatchlistLoading(false);
        setCalendarLoading(false);
    };

    const fetchAndUpdateRightEarningsEvents = async (data) => {
        const rightEarningsEvents = await fetchEarningsEvents(data);
        if (activeWatchlists.length !== 0) {
            setRightEarningsEvent(rightEarningsEvents);
        } else {
            setRightEarningsEvent([]);
        }
    };

    const fetchAndUpdateDB = async (data) => {

        if(googleFlag=="true"){
        addICSDataGoogle(data);}

        else if(outlookFlag=="true"){
        addICSDataOutlook(data);
        }

        else{
        addICSDataGoogle(data);
        addICSDataOutlook(data);
        }


        //const p = await getUserAccounts();
        /*
        if (activeWatchlists.length !== 0) {
        
            for (let i in activeWatchlists){
                if
            }
            setRightEarningsEvent(rightEarningsEvents);
        } else {
            setRightEarningsEvent([]);
        }
        */
       //const client = require("pg/lib/native/client");
       /*
        if (activeWatchlists.length !== 0) {
            setRightEarningsEvent(rightEarningsEvents);
        } else {
            setRightEarningsEvent([]);
        }
        */

  

    //const p = await getUserAccounts();
    /*
    if (activeWatchlists.length !== 0) {
    
        for (let i in activeWatchlists){
            if
        }
        setRightEarningsEvent(rightEarningsEvents);
    } else {
        setRightEarningsEvent([]);
    }
    */
   //const client = require("pg/lib/native/client");
   /*
    if (activeWatchlists.length !== 0) {
        setRightEarningsEvent(rightEarningsEvents);
    } else {
        setRightEarningsEvent([]);
    }
    */


};

    const addDays = (date, days) => {
        var result = new Date(parseInt(date) * 1000);
        result.setDate(result.getDate() + days);
        return result / 1000;
    };


    useEffect(() => {
        if (startTSCx[0] && endTSCx[0] && activeWatchlists) {
            window.localStorage.setItem('activeWatchlists', JSON.stringify(activeWatchlists));
            setRightEarningsEventDays(30);
            let data = {
                watch: activeWatchlists,
                startTS: startTSCx[0],
                endTS: endTSCx[0],
                excel: false,
            };
            setIsWatchlistLoading(true);
            fetchWatchlistData(data);

            const jsonData = {
                watch: activeWatchlists,
                startTS: startTSCx[0],
                endTS: addDays(startTSCx[0], 30),
                excel: false,
            };

            fetchAndUpdateRightEarningsEvents(jsonData);
        }
    }, [activeWatchlists]);

    useEffect(() => {

            const jsonData = {
                watch: activeWatchlists,
            };

            fetchAndUpdateDB(jsonData,googleFlag,outlookFlag);
    },[exportactiveWatchlists && googleFlag=="true" && outlookFlag=="true"]);
    useEffect(() => {

        const jsonData = {
            watch: activeWatchlists,
        };

        fetchAndUpdateDB(jsonData,googleFlag,outlookFlag);
    },[exportactiveWatchlists && outlookFlag=="true"]);

    useEffect(() => {

    const jsonData = {
        watch: activeWatchlists,
    };

    fetchAndUpdateDB(jsonData,googleFlag,outlookFlag);
    },[exportactiveWatchlists && googleFlag=="true"]);

    const isCheckedWatchlist = (watchlist) => activeWatchlists.includes(watchlist);
    const onClickWatchlist = async (watchlist) => {
        if (activeWatchlists.includes(watchlist)) {
            let newActiveWatchlists = activeWatchlists.filter((item) => item !== watchlist);
            setActiveWatchlists([...newActiveWatchlists]);
        } else {
            setActiveWatchlists([...activeWatchlists, watchlist]);
        }
    };

    const isCheckedexportWatchlist = (watchlist) => exportactiveWatchlists.includes(watchlist);
    const onClickWatchlist_export = async (watchlist) => {
        if (exportactiveWatchlists.includes(watchlist)) {
            let exportnewActiveWatchlists = exportactiveWatchlists.filter((item) => item !== watchlist);
            setexportActiveWatchlists([...exportnewActiveWatchlists]);
        } else {
            setexportActiveWatchlists([...exportactiveWatchlists, watchlist]);
        }
    };

    const getUserEmail = (provider) => {
       for  (let i in calendars) {
            if (calendars[i].provider == provider) {
                return calendars[i].emailAddress;
            }
        }
    };

    const renderEmailAndLastSyncedSection = (provider) => {
        return (
            <div className="email_time_container">
                <div className="email">{getUserEmail(provider)}</div>
                <div className="last_synced_section">
                    <div className="last_synced_icon"></div>
                    <div className="last_synced">{`Last Synced: ${getLastSyncTime(
                        getUserEmail(provider)
                    )}`}</div>
                </div>
            </div>
        );
    };
    const renderWathclistCheckboxforexport = (watchlists, isLoading) => {
        let returnVal;
        if (watchlists.length <= 3 || isSeeMoreOpen) {
            returnVal = watchlists.map((watchlist) => (
                <div key={watchlist} className="filter_row watchlist_row">
                    <input
                        className="filter_check watchlist_check"
                        onClick={() => {
                            if (isLoading) {
                                return;
                            }
                            onClickWatchlist_export(watchlist);
                        }}
                        checked={isCheckedexportWatchlist(watchlist)}
                        id={watchlist}
                        type="checkbox"
                        value=""
                    />
                    <div
                        class="filter_name watchlist_name"
                        style={{ cursor: 'crosshair' }}
                        onClick={() => {
                            if (isLoading) {
                                return;
                            }
                            onClickWatchlist_export(watchlist);
                        }}
                    >
                        {watchlist}
                    </div>
                </div>
            ));
        } else {
            returnVal = watchlists.map((watchlist, index) => {
                if (index <= 2) {
                    return (
                        <div key={watchlist} className="filter_row watchlist_row">
                            <input
                                className="filter_check watchlist_check"
                                onClick={() => {
                                    if (isLoading) {
                                        return;
                                    }
                                    onClickWatchlist_export(watchlist);
                                }}
                                checked={isCheckedexportWatchlist(watchlist)}
                                id={watchlist}
                                type="checkbox"
                                value=""
                            />
                            <div
                                class="filter_name watchlist_name"
                                style={{ cursor: 'crosshair' }}
                                onClick={() => {
                                    if (isLoading) {
                                        return;
                                    }
                                    onClickWatchlist_export(watchlist);
                                }}
                            >
                                {watchlist}
                            </div>
                        </div>
                    );
                }
            });
        }
        return returnVal;
    };

    const renderWathclistCheckbox = (watchlists, isLoading) => {
        let returnVal;
        if (watchlists.length <= 3 || isSeeMoreOpen) {
            returnVal = watchlists.map((watchlist) => (
                <div key={watchlist} className="filter_row watchlist_row">
                    <input
                        className="filter_check watchlist_check"
                        onClick={() => {
                            if (isLoading) {
                                return;
                            }
                            onClickWatchlist(watchlist);
                        }}
                        checked={isCheckedWatchlist(watchlist)}
                        id={watchlist}
                        type="checkbox"
                        value=""
                    />
                    <div
                        class="filter_name watchlist_name"
                        style={{ cursor: 'crosshair' }}
                        onClick={() => {
                            if (isLoading) {
                                return;
                            }
                            onClickWatchlist(watchlist);
                        }}
                    >
                        {watchlist}
                    </div>
                </div>
            ));
        } else {
            returnVal = watchlists.map((watchlist, index) => {
                if (index <= 2) {
                    return (
                        <div key={watchlist} className="filter_row watchlist_row">
                            <input
                                className="filter_check watchlist_check"
                                onClick={() => {
                                    if (isLoading) {
                                        return;
                                    }
                                    onClickWatchlist(watchlist);
                                }}
                                checked={isCheckedWatchlist(watchlist)}
                                id={watchlist}
                                type="checkbox"
                                value=""
                            />
                            <div
                                class="filter_name watchlist_name"
                                style={{ cursor: 'crosshair' }}
                                onClick={() => {
                                    if (isLoading) {
                                        return;
                                    }
                                    onClickWatchlist(watchlist);
                                }}
                            >
                                {watchlist}
                            </div>
                        </div>
                    );
                }
            });
        }
        return returnVal;
    };

    return (
        <div id="all_calenders_menu">
            <div className="calendar_section">
                <div className="sentieo_watchlist">
                    <input
                        className="bulk_watchlist_checkbox"
                        checked={calendarBulkAction}
                        type="checkbox"
                        value=""
                        onClick={() => onClickBulkCalendarCheckbox(!calendarBulkAction)}
                    />
                    <div
                        className="all_calenders_head"
                        onClick={() => onClickBulkCalendarCheckbox(!calendarBulkAction)}
                        style={{ cursor: 'pointer' }}
                    >
                        My Calendar
                    </div>
                    <div className="clear_all_button" onClick={onClickCalendarClearAllButton}>
                        Clear All
                    </div>
                </div>
                <div className="all_calenders" style={{ margin: '2px' }}>
                    <div id="add_account_section">
                        <ButtonNew
                            onClick={() => {
                                setShowType(true);
                            }}
                        >
                            <div className="add_button_icon"></div>
                            <div id="add_account_button">Add Accounts</div>
                        </ButtonNew>
                    </div>
                </div>

                <div className="calendar_section">
                {isexportWatchlistLoading ? (
                    <div className="blurred">
                        <div className="sentieo_watchlist_container">
                            <div className="section_head">Export Watchlists
                            <div className="all_calenders_head" style={{ cursor: 'pointer' }}>
                                Google Calendar
                                <FontAwesomeIcon
                                style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                            />
                            </div>
                            <div className="all_calenders_head" style={{ cursor: 'pointer' }}>
                                Outlook Calendar
                                <FontAwesomeIcon
                                style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                            />
                            </div>
                            </div>
                            <FontAwesomeIcon
                                style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                                icon={WatchlistOpen ? faChevronDown : faChevronRight}
                            />
                        </div>
                        {WatchlistOpen && renderWathclistCheckboxforexport(watchlists, true)}
                    </div>
                ) : (
                    <>
                        
                        <div className="sentieo_watchlist_container">
                            <div className="section_head">Export Watchlists
                            <div className="all_calenders_head" style={{ cursor: 'pointer' }}>
                                Google Calendar
                                <FontAwesomeIcon
                                style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                                icon={WatchlistOpen ? faChevronDown : faChevronRight}
                                onClick={() => (setWatchlistOpen(!WatchlistOpen) && setGoogleFlag("true"))}
                            />
                            </div>
                            <div className="all_calenders_head" style={{ cursor: 'pointer' }}>
                                Outlook Calendar
                                <FontAwesomeIcon
                                style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                                icon={WatchlistOpen ? faChevronDown : faChevronRight}
                                onClick={() => (setWatchlistOpen(!WatchlistOpen) && setOutlookFlag("true"))}
                            />
                            </div>
                            </div>
                            <FontAwesomeIcon
                                style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                                icon={WatchlistOpen ? faChevronDown : faChevronRight}
                                onClick={() => (setWatchlistOpen(!WatchlistOpen) && setGoogleFlag("true") && setOutlookFlag("true"))}
                            />
                        </div>
                        {WatchlistOpen && renderWathclistCheckboxforexport(watchlists)}
                    </>
                )}
                {WatchlistOpen && watchlists.length >= 3 ? (
                    <div
                        className="showlessmore"
                        onClick={() => {
                            setIsSeeMoreOpen(!isSeeMoreOpen);
                        }}
                    >
                        {isSeeMoreOpen ? 'View Less' : 'View More'}
                    </div>
                ) : null}
            </div>

                {isAvailable('graph') && (
                    <div className="sentieo_watchlist_container">
                        <div className="mail_container">
                            <div className="mail_icon"></div>
                            <div className="section_head">Outlook</div>
                        </div>
                        <FontAwesomeIcon
                            style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                            icon={isOutlookCalendarOpen ? faChevronDown : faChevronRight}
                            onClick={() => setIsOutlookCalendarOpen(!isOutlookCalendarOpen)}
                        />
                    </div>
                )}

                {isAvailable('graph') && renderEmailAndLastSyncedSection('graph')}

                {isOutlookCalendarOpen && (
                    <AllCalenders
                        color={props.color}
                        provide="graph"
                        addAnAccount={props.addAnAccount}
                        calendars={calendars}
                        getCalendarEvents={props.getCalendarEvents}
                    />
                )}

                {isAvailable('gmail') && (
                    <div className="sentieo_watchlist_container">
                        <div className="mail_container">
                            <div className="mail_icon"></div>
                            <div className="section_head">Gmail</div>
                        </div>
                        <FontAwesomeIcon
                            style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                            icon={isGmailCalendarOpen ? faChevronDown : faChevronRight}
                            onClick={() => setIsGmailCalendarOpen(!isGmailCalendarOpen)}
                        />
                    </div>
                )}

                {isAvailable('gmail') && renderEmailAndLastSyncedSection('gmail')}

                {isGmailCalendarOpen && (
                    <AllCalenders
                        color={props.color}
                        provide="gmail"
                        addAnAccount={props.addAnAccount}
                        calendars={calendars}
                        getCalendarEvents={props.getCalendarEvents}
                    />
                )}
            </div>
            <div className="calendar_section">
                {isWatchlistLoading ? (
                    <div className="blurred">
                        <div className="sentieo_watchlist">
                            <input
                                className="bulk_watchlist_checkbox"
                                checked={sentieoWatchlist}
                                type="checkbox"
                                value=""
                            />
                            <div className="all_calenders_head" style={{ cursor: 'pointer' }}>
                                Sentieo Calendar
                            </div>
                            <div className="clear_all_button">Clear All</div>
                        </div>
                        <div className="sentieo_watchlist_container">
                            <div className="section_head">Watchlists</div>
                            <FontAwesomeIcon
                                style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                                icon={isWatchlistOpen ? faChevronDown : faChevronRight}
                            />
                        </div>
                        {isWatchlistOpen && renderWathclistCheckbox(watchlists, true)}
                    </div>
                ) : (
                    <>
                        <div className="sentieo_watchlist">
                            <input
                                className="bulk_watchlist_checkbox"
                                checked={sentieoWatchlist}
                                type="checkbox"
                                value=""
                                onClick={() => onClickBulkWatchlistCheckbox(!sentieoWatchlist)}
                            />
                            <div
                                className="all_calenders_head"
                                onClick={() => onClickBulkWatchlistCheckbox(!sentieoWatchlist)}
                                style={{ cursor: 'pointer' }}
                            >
                                Sentieo Calendar
                            </div>
                            <div className="clear_all_button" onClick={onClickClearAllButton}>
                                Clear All
                            </div>
                        </div>
                        <div className="sentieo_watchlist_container">
                            <div className="section_head">Watchlists</div>
                            <FontAwesomeIcon
                                style={{ fontSize: '10px', cursor: 'pointer', color: '#506F8A' }}
                                icon={isWatchlistOpen ? faChevronDown : faChevronRight}
                                onClick={() => setIsWatchlistOpen(!isWatchlistOpen)}
                            />
                        </div>
                        {isWatchlistOpen && renderWathclistCheckbox(watchlists)}
                    </>
                )}
                {isWatchlistOpen && watchlists.length >= 3 ? (
                    <div
                        className="showlessmore"
                        onClick={() => {
                            setIsSeeMoreOpen(!isSeeMoreOpen);
                        }}
                    >
                        {isSeeMoreOpen ? 'View Less' : 'View More'}
                    </div>
                ) : null}
            </div>
            {showType ? <CalendarWizard pageState={1} setShowType={setShowType} /> : null}

            
        </div>
    );
}

export default MenuMain;
