import requests

class RiotApiService:
    def __init__(self,api_key):
        self.api_key = api_key
        self.base_url = "https://europe.api.riotgames.com"
        self.try_url = "https://euw1.api.riotgames.com"

    def headers(self):
        return {"X-Riot-Token": self.api_key}

    def get_account_by_riot_id(self, game_name, tag_line):
        url = f"{self.base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        print(url)
        resp = requests.get(url, headers=self.headers())
        resp.raise_for_status()
        return resp.json() 

    def get_summoner_by_puuid(self, puuid):
        url = f"{self.try_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        resp = requests.get(url, headers=self.headers())

        resp.raise_for_status()
        return resp.json()

    def get_match_ids_by_puuid(self, puuid, count):
        url = f"{self.base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
        resp = requests.get(url, headers=self.headers())

        resp.raise_for_status()
        return resp.json()

    def get_match_by_id(self, match_id):
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}"
        resp = requests.get(url, headers=self.headers())
        resp.raise_for_status()
        return resp.json()

    def get_rank(self, puuid):
        url = f"{self.try_url}/lol/league/v4/entries/by-puuid/{puuid}"
        resp = requests.get(url, headers=self.headers())
        resp.raise_for_status()
        entries = resp.json() 

        ranks = {}
        for e in entries:
            queue = e["queueType"]
            if queue == 'RANKED_SOLO_5x5':
                return e["tier"]
        return None
    
    

    """ OUTDATED BY RIOT API
    
    def get_active_game_by_puuid(self, puuid):                   
        url = f"{self.try_url}/lol/spectator/v5/active-games/by-summoner/{puuid}"
        try:
            resp = requests.get(url, headers=self.headers())
            resp.raise_for_status()
            print(resp.json())
            return resp.json()
        except requests.HTTPError as e:
            if resp.status_code == 404:
                return None  
            raise e
    """


    def crawl_matches(self, start_puuid, total_matches):
        visited_matches = set()
        puuid_queue = [start_puuid]
        matches_data = []

        while len(matches_data) < total_matches and puuid_queue:
            puuid = puuid_queue.pop(0)
            try:
                match_ids = self.get_match_ids_by_puuid(puuid, count=3)
            except requests.RequestException as e: 
                print(f"Fehler beim Abrufen von Matches für {puuid}: {e}")
                continue

            for mid in match_ids:
                if mid in visited_matches:
                    continue
                visited_matches.add(mid)

                match_data = self.get_match_by_id(mid)
                matches_data.append(match_data)
                print(f"Fetched match {len(matches_data)}: {mid}")

                participants = match_data["info"]["participants"]
                for p in participants:
                    p_puuid = p["puuid"]
                    if p_puuid not in puuid_queue and p_puuid != puuid:
                        puuid_queue.append(p_puuid)

                if len(matches_data) >= total_matches:
                    break

        return matches_data


        