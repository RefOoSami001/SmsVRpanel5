def get_panel_code(number):
    import re
    import requests
    import json
    cookies = {
        'PHPSESSID': 'nvlvbb5ro1u8p6p3rr126sldc5',
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        # 'Cookie': 'PHPSESSID=nvlvbb5ro1u8p6p3rr126sldc5',
        'Referer': 'http://109.236.81.102/ints/agent/SMSCDRStats',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }


    response = requests.get(
        f'http://109.236.81.102/ints/agent/res/data_smscdr.php?fdate1=2024-10-04%2000:00:00&fdate2=2024-10-04%2023:59:59&frange=&fclient=&fnum={number}&fcli=&fgdate=&fgmonth=&fgrange=&fgclient=&fgnumber=&fgcli=&fg=0&sEcho=1&iColumns=9&sColumns=%2C%2C%2C%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=25&mDataProp_0=0&sSearch_0=&bRegex_0=false&bSearchable_0=true&bSortable_0=true&mDataProp_1=1&sSearch_1=&bRegex_1=false&bSearchable_1=true&bSortable_1=true&mDataProp_2=2&sSearch_2=&bRegex_2=false&bSearchable_2=true&bSortable_2=true&mDataProp_3=3&sSearch_3=&bRegex_3=false&bSearchable_3=true&bSortable_3=true&mDataProp_4=4&sSearch_4=&bRegex_4=false&bSearchable_4=true&bSortable_4=true&mDataProp_5=5&sSearch_5=&bRegex_5=false&bSearchable_5=true&bSortable_5=true&mDataProp_6=6&sSearch_6=&bRegex_6=false&bSearchable_6=true&bSortable_6=true&mDataProp_7=7&sSearch_7=&bRegex_7=false&bSearchable_7=true&bSortable_7=true&mDataProp_8=8&sSearch_8=&bRegex_8=false&bSearchable_8=true&bSortable_8=false&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1&_=1728052116864',
        cookies=cookies,
        headers=headers,
    )
    # try:
    print(response.text)
    data = json.loads(response.text)
    print(data)
    # Extract the message
    message_text = data['aaData'][0][5]

    verification_code = re.search(r'\d+', message_text)
        
    if verification_code:
        return verification_code.group()
    else:
        return None
    # except:
    #     return None
    
code = get_panel_code('50245731974')
print(code)