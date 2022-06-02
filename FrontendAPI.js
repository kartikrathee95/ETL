
import axios from 'axios';

import Core from 'core';

export async function addICSDataGoogle(watch) {
    
    const url = `https://testingintegrationservice.sentieo.com/api/onenote/exportWatchlistsGoogle`
    const BACKEND_URL = Core.integrations_env;
    let response = {};
    await fetch(url, {
        method: 'post',
        //body: JSON.stringify(watch),
        //credentials: 'include',
    })
        .then(async (response) => response.json())
        .then((res) => {
            response = res;
        })
        .catch((err) => {
            console.error(err);
        });
    return response;
}

export async function addICSDataOutlook(watch) {
    
    const url = `https://testingintegrationservice.sentieo.com/api/onenote/exportWatchlistsOutlook`
    const BACKEND_URL = Core.integrations_env;
    let response = {};
    await fetch(url, {
        method: 'post',
        //body: JSON.stringify(watch),
        //credentials: 'include',
    })
        .then(async (response) => response.json())
        .then((res) => {
            response = res;
        })
        .catch((err) => {
            console.error(err);
        });
    return response;
}
