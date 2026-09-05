import { SongCard, type DealtTrack } from './SongCard'

const TABLE_FAN: DealtTrack[] = [
  {
    spotify_id: 'preview-gun-to-my-head',
    name: 'Gun to My Head',
    artist_name: 'Malcolm Todd',
    album_name: 'Do That Again',
    url: 'https://open.spotify.com/search/Gun%20to%20My%20Head%20Malcolm%20Todd',
    image_url: '/covers/gun-to-my-head.jpg',
  },
  {
    spotify_id: 'preview-hype-boy',
    name: 'Hype Boy',
    artist_name: 'NewJeans',
    album_name: "NewJeans 1st EP 'New Jeans'",
    url: 'https://open.spotify.com/search/Hype%20Boy%20NewJeans',
    image_url: '/covers/hype-boy.jpg',
  },
  {
    spotify_id: 'preview-16',
    name: '16',
    artist_name: 'Baby Keem',
    album_name: 'The Melodic Blue',
    url: 'https://open.spotify.com/search/16%20Baby%20Keem',
    image_url: '/covers/16.jpg',
  },
  {
    spotify_id: 'preview-sweater-weather',
    name: 'Sweater Weather',
    artist_name: 'The Neighbourhood',
    album_name: 'I Love You.',
    url: 'https://open.spotify.com/search/Sweater%20Weather%20The%20Neighbourhood',
    image_url: '/covers/sweater-weather.jpg',
  },
  {
    spotify_id: 'preview-a-cold-play',
    name: 'A COLD PLAY',
    artist_name: 'The Kid LAROI',
    album_name: 'A COLD PLAY',
    url: 'https://open.spotify.com/search/A%20COLD%20PLAY%20The%20Kid%20LAROI',
    image_url: '/covers/a-cold-play.jpg',
  },
]

export function TableFan() {
  return (
    <div className="row-deck" aria-hidden="true">
      {TABLE_FAN.map((track, index) => (
        <SongCard
          key={track.spotify_id}
          track={track}
          index={index}
          isFront={index === 0}
          peekOffset={index}
          layout="row"
          playable={false}
        />
      ))}
    </div>
  )
}
