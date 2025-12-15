import { useState } from "react";
import "./index.css";


const url = 'http://localhost:5000/api/';
type Summoner = {
  name: string;
};

interface Participant {
  teamId?: number;
  championName: string;
  summonerName: string;
  win: boolean;
}

interface RecentGame {
  matchId: string;
  participants: Participant[];

}

function App() {
  const [gameName, setGameName] = useState("");
  const [tagLine, setTagLine] = useState("");
  const [rankedGamesCount,setRankedGamesCount]  = useState<number>(0)
  const [predictionResults, setPredictionResults] = useState<{[matchId: string]: string}>({});
  const [summoner, setSummoner] = useState<Summoner | null>(null);
  const [recentGames, setRecentGames] = useState<RecentGame[]>([]);
  const [canLoadMatches, setCanLoadMatches] = useState(true);
  const [cooldown, setCooldown] = useState(0);

  const loadSummoner = async () => {
    if (!canLoadMatches) return;
    if (!gameName || !tagLine) return;

      setCanLoadMatches(false);
      setCooldown(2); 

      const interval = setInterval(() => {
        setCooldown(prev => {
          if (prev <= 1) {
            clearInterval(interval);
            setCanLoadMatches(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);


    const res = await fetch(
      url + `/summoner?gameName=${gameName}&tagLine=${tagLine}`
    );

    if (res.ok) {
      const currentSummoner = gameName + "#" + tagLine;
      setSummoner({ name: currentSummoner});
    } else {
      console.error("API request failed", res.status);
      setSummoner(null);
      return;
    }

    const res2 = await fetch(
     url + `/recent-games?gameName=${gameName}&tagLine=${tagLine}`
    );

    if (res2.ok) {
      const data = await res2.json();
      setRecentGames(data.recentGames); 
      setRankedGamesCount(data.rankedGamesCount);
    }
  };

  const getChampionIcon = (championName: string) => {
    const version = "15.24.1"; 
    return `https://ddragon.leagueoflegends.com/cdn/${version}/img/champion/${championName}.png`;
  };

  function splitByWinningTeam(participants: Participant[]) {
    const winners: Participant[] = [];
    const losers: Participant[] = [];

    participants.forEach(p => {
      if (p.win) {
        winners.push(p);
      } else {
        losers.push(p);
      }
    });

  return { winners, losers };
}




const handlePredict = async (matchId: string, winners: Participant[], losers: Participant[]) => {
  const team1: string[] = winners.map(p => p.championName);
  const team2: string[] = losers.map(p => p.championName);

  const res = await fetch(url + `/predict?team1=${team1}&team2=${team2}`);
  const prediction = await res.json(); 

  const isCurrentInTeam2 = losers.some(p => p.summonerName === summoner?.name);

  const adjustedPrediction = isCurrentInTeam2 ? (1 - prediction)*100 : prediction*100;

  setPredictionResults(prev => ({ ...prev, [matchId]: adjustedPrediction.toFixed(3) }));
};



return (
  <div className = "header-font">
    <h1>Predict League</h1>

    <div style={{ marginBottom: 20 }}>
      <input
        value={gameName}
        onChange={(e) => setGameName(e.target.value)}
        placeholder="Game Name"
        style={{ marginRight: 10 }}
      />
      <input
        value={tagLine}
        onChange={(e) => setTagLine(e.target.value)}
        placeholder="Tag Line"
        style={{ marginRight: 10 }}
      />
      <button onClick={loadSummoner}>  {canLoadMatches ? "Load Summoner" : `Please wait ${cooldown}s`}</button>
    </div>

    <div className = "font-render">
      Current Summoner: {summoner?.name || "–"}
      <p>Ranked Solo 5 vs 5 games loaded: {rankedGamesCount}</p>
    </div>

    {recentGames.length === 0 && <div>No recent games loaded</div>}


     {recentGames.map((game, idx) => {
  const { winners, losers } = splitByWinningTeam(game.participants);

  return (
    <div key={idx} className="match">

      <div className="teams">

<ul className="participants-list team-left">
  {winners.map((p, i) => {
    const isCurrentUser = p.summonerName.toLowerCase() === summoner?.name.toLowerCase();
    console.log(summoner?.name);
    console.log(p.summonerName)
    return (
      <li
        key={i}
        className={`participant team-blue ${isCurrentUser ? "current-user" : ""}`}
      >
        <img
          src={getChampionIcon(p.championName)}
          alt={p.championName}
          className={`champion-icon ${isCurrentUser ? "current-user-icon" : ""}`}
        />
        <span>{p.championName}</span>
      </li>
    );
  })}
</ul>
        <ul className="participants-list team-right">
        {losers.map((p, i) => {
          const isCurrentUser = p.summonerName.toLowerCase() === summoner?.name.toLowerCase();
          return (
            <li
              key={i}
              className={`participant team-red ${isCurrentUser ? "current-user" : ""}`}
            >
              <img
                src={getChampionIcon(p.championName)}
                alt={p.championName}
                className={`champion-icon ${isCurrentUser ? "current-user-icon" : ""}`}
              />
              <span>{p.championName}</span>
            </li>
          );
        })}
      </ul>
        {predictionResults[game.matchId] == null ? (
          <button
            className="predict-button"
            onClick={() => handlePredict(game.matchId, winners, losers)}
          >
            Predict outcome based on Champion Picks
          </button>
        ) : (
          <div className="predict-result">
                Prediction that your team would have won based on champion picks:{" "}
                <span style={{ color: Number(predictionResults[game.matchId]) > 50 ? "green" : "red" }}>{predictionResults[game.matchId]}</span>%
          </div>
        )}
      </div>
    </div>
  );
})}



  </div>
);

}

export default App;
