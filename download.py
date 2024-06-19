
from bs4 import BeautifulSoup
import html
import json
import os
import re
import unicodedata
import requests
import xmltodict

with open('settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)

cookies = settings['cookies']
base_url = settings['url']
tenant_id = settings['tenant']
last_record = settings['lastRecord']

class NotFoundException(Exception):
    pass

class TagNotFoundException(Exception):
    pass

def slugify(value, allow_unicode=False):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')

    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def find_tag_by_tag(data_dict: dict, tag: str):
    for datafield in data_dict['collection']['record']['datafield']:
        if datafield['@tag'] == tag:
            return datafield['subfield']

    raise TagNotFoundException(f'Invalid tag: {tag}')

def find_subfield(subfields: list, code: str):
    for subfield in subfields:
        if subfield['@code'] == code:
            return subfield['#text']

    raise TagNotFoundException(f'Invalid subfield: {code}')

def find_author(data_dict: dict):
    subfields = find_tag_by_tag(data_dict, '100')

    try:
        return subfields['#text']
    except:
        return find_subfield(subfields, 'a')

def find_title(data_dict: dict):
    subfields = find_tag_by_tag(data_dict,'245')

    try:
        return find_subfield(subfields, 'a')
    except:
        return find_subfield(subfields, 'h')

def find_year(data_dict: dict):
    subfield = find_tag_by_tag(data_dict, '260')

    if isinstance(subfield, list):
        return find_subfield(subfield, 'c')
    else:
        return subfield['#text']

def download_xml(record_id: int):
    link = f'{base_url}/ro/record'
    params = {
        'p_p_id': 'DisplayRecord_WAR_akfweb',
        'p_p_lifecycle': '2',
        'p_p_state': 'normal',
        'p_p_mode': 'view',
        'p_p_resource_id': 'getRecord',
        'p_p_cacheability': 'cacheLevelPage',
        'p_p_col_id': 'column-2',
        'p_p_col_count': '2',
        '&_DisplayRecord_WAR_akfweb_implicitModel': 'true'
    }
    form_data = {
        'recordId': f'RECORD{record_id}',
        'dbid': 'solr',
        'recordType':   'manifestation',
        'format': 'marcxml.html',
        'fromOutside': 'false'
    }
    headers = {
        'Accept': 'text/html, */*; q=0.01',
        'User-Agent': 'Mozilla/5.0'
    }

    response = requests.post(link, params=params, data=form_data, cookies=cookies, headers=headers, timeout=5)
    response_text = html.unescape(response.text)

    if 'nu a fost găsită!' in response_text:
        raise NotFoundException()

    response_text = response_text.replace('<div class="MarcXMLBox">', '').replace('</div>', '').replace('<br />', '')
    response_text = response_text.strip()

    try:
        data_dict = xmltodict.parse(response_text)
    except Exception as e:
        print('Error parsing XML!')
        print(response_text)
        raise NotFoundException() from e

    filename = os.path.join('records', f'{record_id}.json')

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, indent=2, ensure_ascii=False)

    return data_dict

def find_pdfs(record_id):
    link = f'{base_url}/media-provider-webapp/fragments/default/RECORD{record_id}'
    params = {
        'tenant_id': tenant_id,
        'viewType': 'fotorama'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(link, params=params, headers=headers, cookies=cookies, timeout=5)
    filename = os.path.join('medias', f'{record_id}.html')

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    pdf_media_ids = set()

    for a in soup.find_all('span', {'class': 'fotorama_pdf_wrapper'}):
        thumb = a['data-thumb']
        pdf_media_id = re.search(r'mediaId=(\d+)', thumb)

        if not pdf_media_id:
            raise Exception(f'No media ID: {thumb}')

        pdf_media_id = int(pdf_media_id.group(1))
        pdf_media_ids.add(pdf_media_id)

    return list(pdf_media_ids)

def download_media(record_id: int, media_id: int, filename: str):
    if os.path.exists(filename):
        return

    link = f'{base_url}/media-provider-webapp/rest/file/mastermedia/default/RECORD{record_id}'
    params = {'mediaId': str(media_id), 'tenant_id': tenant_id}

    with requests.get(link, cookies=cookies, params=params, timeout=10, stream=True) as response:
        response.raise_for_status()

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=65536):
                f.write(chunk)

if __name__ == '__main__':
    folders = ['pdfs', 'records', 'medias']

    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    for record_id in range(last_record, 1, -1):
        print('Handling record number', record_id)
        print('Downloading XML...')

        try:
            data_dict = download_xml(record_id)
        except NotFoundException:
            print('Record not found.')
            continue

        print(data_dict)
        print('Finding PDFs...')

        media_ids = find_pdfs(record_id)

        if not media_ids:
            continue

        print('Media IDs:', media_ids)

        try:
            author = find_author(data_dict)
        except TagNotFoundException:
            print('Failed to find author:', data_dict)
            continue

        try:
            title = find_title(data_dict)
        except TagNotFoundException:
            print('Failed to find title:', data_dict)
            continue

        try:
            year = find_year(data_dict)
        except TagNotFoundException:
            print('Failed to find year:', data_dict)
            continue

        for media_id in media_ids:
            media_filename = f'{record_id}-{media_id}-{year}-{slugify(author)}-{slugify(title)}'[:250]
            media_filename = os.path.join('pdfs', f'{media_filename}.pdf')
            print('Downloading', media_filename)
            download_media(record_id, media_id, media_filename)
