/**
 * Natural Language Query Component
 * Allows users to ask questions about their analytics data in natural language
 */

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User, 
  Lightbulb,
  BarChart3,
  TrendingUp,
  Clock,
  Loader2
} from 'lucide-react';

import { useAIInsights } from '@/hooks/useAIInsights';

interface QueryMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  data?: any;
  suggestions?: string[];
}

interface NaturalLanguageQueryProps {
  clientId: string;
}

export const NaturalLanguageQuery: React.FC<NaturalLanguageQueryProps> = ({ 
  clientId 
}) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<QueryMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { processNaturalLanguageQuery } = useAIInsights();

  // Sample suggestions for getting started
  const sampleQuestions = [
    "What's my bounce rate this week?",
    "How many sessions did I have yesterday?",
    "Show me conversion rate trends",
    "What's causing the traffic spike?",
    "Which pages have the highest bounce rate?",
    "Compare this month's performance to last month"
  ];

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isProcessing) return;

    const userMessage: QueryMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: query.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsProcessing(true);

    try {
      const response = await processNaturalLanguageQuery({
        query: userMessage.content,
        client_id: clientId
      });

      const aiMessage: QueryMessage = {
        id: `ai_${Date.now()}`,
        type: 'ai',
        content: response.answer,
        timestamp: new Date(),
        data: response.data,
        suggestions: response.suggestions
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: QueryMessage = {
        id: `ai_error_${Date.now()}`,
        type: 'ai',
        content: 'Sorry, I encountered an error processing your query. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    inputRef.current?.focus();
  };

  const renderMessage = (message: QueryMessage) => {
    const isUser = message.type === 'user';
    
    return (
      <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-2`}>
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-primary text-primary-foreground ml-2' : 'bg-muted mr-2'
          }`}>
            {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </div>
          
          <div className={`rounded-lg p-3 ${
            isUser 
              ? 'bg-primary text-primary-foreground' 
              : 'bg-muted'
          }`}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            
            {/* Display data if available */}
            {message.data && Object.keys(message.data).length > 0 && (
              <div className="mt-3 p-2 bg-background/10 rounded border">
                <div className="flex items-center mb-2">
                  <BarChart3 className="h-3 w-3 mr-1" />
                  <span className="text-xs font-medium">Data</span>
                </div>
                {Object.entries(message.data).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="capitalize">{key.replace('_', ' ')}:</span>
                    <span className="font-mono">
                      {Array.isArray(value) 
                        ? `[${value.slice(-3).join(', ')}...]` 
                        : typeof value === 'number' 
                          ? value.toLocaleString() 
                          : String(value)
                      }
                    </span>
                  </div>
                ))}
              </div>
            )}
            
            {/* Display suggestions */}
            {message.suggestions && message.suggestions.length > 0 && (
              <div className="mt-3">
                <div className="flex items-center mb-2">
                  <Lightbulb className="h-3 w-3 mr-1" />
                  <span className="text-xs font-medium">Try asking:</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {message.suggestions.map((suggestion, index) => (
                    <Button
                      key={index}
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex items-center justify-end mt-2">
              <div className="flex items-center text-xs opacity-70">
                <Clock className="h-3 w-3 mr-1" />
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          AI Analytics Assistant
        </CardTitle>
        <CardDescription>
          Ask questions about your analytics data in natural language
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages Area */}
        <ScrollArea className="flex-1 p-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Bot className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
              <p className="text-muted-foreground mb-6 max-w-md">
                Ask me anything about your analytics data. I can help you understand trends, 
                identify issues, and provide insights.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-lg">
                <div className="text-xs text-muted-foreground mb-2 col-span-full">
                  Try these sample questions:
                </div>
                {sampleQuestions.map((question, index) => (
                  <Badge 
                    key={index}
                    variant="outline" 
                    className="cursor-pointer hover:bg-muted text-xs p-2 h-auto whitespace-normal"
                    onClick={() => handleSuggestionClick(question)}
                  >
                    {question}
                  </Badge>
                ))}
              </div>
            </div>
          ) : (
            <div>
              {messages.map(renderMessage)}
              {isProcessing && (
                <div className="flex justify-start mb-4">
                  <div className="flex items-start space-x-2">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="bg-muted rounded-lg p-3">
                      <div className="flex items-center space-x-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">Analyzing your data...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <Input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask me about your analytics data..."
              className="flex-1"
              disabled={isProcessing}
            />
            <Button 
              type="submit" 
              disabled={!query.trim() || isProcessing}
              size="sm"
            >
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
          
          <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
            <div className="flex items-center space-x-4">
              <span>Powered by AI</span>
              <Badge variant="outline" className="text-xs">
                Beta
              </Badge>
            </div>
            <span>Press Enter to send</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};