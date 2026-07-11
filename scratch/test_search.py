import requests

def search_easyeda(keyword):
    url = "https://pro.lceda.cn/api/components/search"
    payload = {
        "searchKeyword": keyword,
        "type": 1,
        "returnList": True
    }
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        data = resp.json()
        print("Status Code:", resp.status_code)
        
        if data.get('success'):
            lst = data.get('result', [])
            if lst:
                print(f"Found {len(lst)} components for {keyword}.")
                for item in lst[:1]:
                    print("Mapped to LCSC:", item.get('attributes', {}).get('Supplier Part', None) or item.get('number'))
                    # try to extract C number from attributes or title
                    print("Title:", item.get('title'))
                    print("Attributes:", item.get('attributes'))
            else:
                print("No results found in list for", keyword)
        else:
            print("Response:", data)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    search_easyeda("AP2112K-3.3TRG1")
    search_easyeda("DRV8835DSSR")
