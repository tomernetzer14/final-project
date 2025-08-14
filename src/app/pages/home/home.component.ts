import { Component , ViewChild } from '@angular/core';
import { ArticleInputComponent } from '../../components/article-input/article-input.component';

@Component({
  selector: 'app-home',
  standalone: false,
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent {
    showApp = false;

    @ViewChild(ArticleInputComponent)
    articleInputComponent!: ArticleInputComponent;
  

  startApp() {
    this.showApp = true;
  }

  goBackToIntro() {
  if (this.articleInputComponent) {
    this.articleInputComponent.onClear();
  }
  this.showApp = false;
}
}
