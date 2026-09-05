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
]

export function TableFan() {
  return (
    <div className="fan" aria-hidden="true">
      {TABLE_FAN.map((track, index) => (
        <SongCard
          key={track.spotify_id}
          track={track}
          index={index}
          isFront
          peekOffset={index}
          layout="fan"
          playable={false}
        />
      ))}
    </div>
  )
}
