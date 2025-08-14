import { Component, OnInit } from '@angular/core';
import { SimplifyService } from '../../services/simplify.service';

@Component({
  selector: 'app-article-output',
  standalone: false,
  templateUrl: './article-output.component.html',
  styleUrl: './article-output.component.css'
})
export class ArticleOutputComponent implements OnInit {
  simplifiedText: string = '';
  keywords: { [section: string]: string[] } = {};

  constructor(private simplifyService: SimplifyService) {}

  ngOnInit() {
    this.simplifyService.simplifiedText$.subscribe(text => {
      this.simplifiedText = text;
    });
    this.simplifyService.keywords$.subscribe(kws => {
      this.keywords = kws;
    });
  }
  highlightKeywords(): string {
    if (!this.simplifiedText || !this.keywords) {
      return this.simplifiedText;
    }
  
    let highlighted = this.simplifiedText;
  
    const allKeywords = new Set<string>();
    Object.values(this.keywords).forEach((words: string[]) => {
      words.forEach(word => allKeywords.add(word));
    });
  
    allKeywords.forEach(keyword => {
      const escaped = keyword.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'); 
      const regex = new RegExp(`\\b(${escaped})\\b`, 'gi');
      highlighted = highlighted.replace(regex, '<span class="highlight" title="Keyword">$1</span>');
    });
  
    return highlighted;
  }
}