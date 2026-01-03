import { FeedItem } from "./types";

export const MOCK_FEED: FeedItem[] = [
  {
    id: '1',
    title: 'Stripe/Agent-Toolkit',
    source: 'GitHub',
    type: 'repo',
    url: '#',
    timestamp: '2 mins ago'
  },
  {
    id: '2',
    title: 'LLMs for Coding: A Comprehensive Review',
    source: 'ArXiv',
    type: 'paper',
    url: '#',
    timestamp: '15 mins ago'
  },
  {
    id: '3',
    title: 'The Future of Serverless GPUs',
    source: 'Medium',
    type: 'article',
    url: '#',
    timestamp: '1 hour ago'
  },
  {
    id: '4',
    title: 'facebook/react-strict-dom',
    source: 'GitHub',
    type: 'repo',
    url: '#',
    timestamp: '3 hours ago'
  },
  {
    id: '5',
    title: 'Attention Is All You Need (Revisited)',
    source: 'ArXiv',
    type: 'paper',
    url: '#',
    timestamp: '5 hours ago'
  },
  {
    id: '6',
    title: 'Optimizing Node.js for Cold Starts',
    source: 'Dev.to',
    type: 'article',
    url: '#',
    timestamp: 'Yesterday'
  }
];

export const INITIAL_LOGS = [
  "Initializing DevPulseAI v2 kernel...",
  "Loading configuration from environment...",
  "Connecting to secure signal stream...",
];